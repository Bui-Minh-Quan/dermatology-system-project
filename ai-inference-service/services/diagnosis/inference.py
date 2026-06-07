import base64
import io

import uuid
from pathlib import Path

import numpy as np
import torch

from PIL import Image

from services.diagnosis.state import diagnosis_state

from services.diagnosis.transforms import (
    skin_detector_transform,
    disease_classifier_transform,
    DISEASE_CLASSES_9
)

from services.diagnosis.gradcam import (
    GradCAMWrapper,
    generate_gradcam
)

# =========================================================
# OUTPUT DIRECTORY
# =========================================================

HEATMAP_DIR = Path("static/heatmaps")

HEATMAP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# =========================================================
# MAIN INFERENCE PIPELINE
# =========================================================

async def run_diagnosis(
    image,
    symptoms="",
    body_vector=None
):

    # =====================================================
    # SAFETY CHECKS
    # =====================================================

    if diagnosis_state.gatekeeper is None:
        raise RuntimeError("Gatekeeper model not loaded.")

    if diagnosis_state.disease_classifier is None:
        raise RuntimeError("Disease classifier model not loaded.")

    if diagnosis_state.tokenizer is None:
        raise RuntimeError("Tokenizer not loaded.")

    # =====================================================
    # DEFAULT METADATA
    # =====================================================

    if body_vector is None or len(body_vector) == 0:
        body_vector = [0] * 8

    # =====================================================
    # LOAD IMAGE
    # =====================================================

    pil_image = Image.open(image.file).convert("RGB")

    # =====================================================
    # 1. GATEKEEPER
    # =====================================================

    gatekeeper_tensor = (
        skin_detector_transform(pil_image)
        .unsqueeze(0)
        .to(diagnosis_state.device)
    )

    with torch.inference_mode():

        gate_logits = diagnosis_state.gatekeeper(
            gatekeeper_tensor
        )

        skin_probability = torch.sigmoid(
            gate_logits
        ).item()

    if skin_probability < 0.5:

        return {
            "success": False,
            "error": "Image rejected. No skin detected."
        }

    # =====================================================
    # 2. IMAGE TENSOR
    # =====================================================

    image_tensor = (
        disease_classifier_transform(pil_image)
        .unsqueeze(0)
        .to(diagnosis_state.device)
    )

    # =====================================================
    # 3. METADATA TENSOR
    # =====================================================

    metadata_tensor = torch.tensor(
        [body_vector],
        dtype=torch.float32,
        device=diagnosis_state.device
    )


    # =====================================================
    # 4. TOKENIZE TEXT
    # =====================================================

    encoded_text = diagnosis_state.tokenizer(
        [symptoms],
        padding="max_length",
        truncation=True,
        max_length=64,
        return_tensors="pt"
    )

    encoded_text = {
        key: value.to(diagnosis_state.device)
        for key, value in encoded_text.items()
    }

    # =====================================================
    # 5. TEXT MASK
    # =====================================================

    has_text_mask = torch.tensor(
        [[1.0 if symptoms.strip() else 0.0]],
        dtype=torch.float32,
        device=diagnosis_state.device
    )

    # =====================================================
    # 6. DISEASE CLASSIFICATION
    # =====================================================

    with torch.inference_mode():

        logits = diagnosis_state.disease_classifier(
            image=image_tensor,
            location_vector=metadata_tensor,
            input_ids=encoded_text["input_ids"],
            attention_mask=encoded_text["attention_mask"],
            has_text_mask=has_text_mask
        )

        probabilities = torch.softmax(
            logits,
            dim=1
        )

        confidence = probabilities.max().item()

        predicted_index = torch.argmax(
            probabilities,
            dim=1
        ).item()

        predicted_disease = (
            DISEASE_CLASSES_9[predicted_index]
        )

    # =====================================================
    # 7. GRADCAM
    # =====================================================

    gradcam_wrapper = GradCAMWrapper(
        model=diagnosis_state.disease_classifier,
        location_vector=metadata_tensor,
        input_ids=encoded_text["input_ids"],
        attention_mask=encoded_text["attention_mask"],
        has_text_mask=has_text_mask
    )

    # IMPORTANT:
    # Ensure this layer exists in your model architecture

    target_layer = (
        gradcam_wrapper
        .model
        .image_encoder
        .features[7]
    )

    # =====================================================
    # 8. ORIGINAL IMAGE
    # =====================================================

    original_image = (
        np.array(
            pil_image.resize((384, 384))
        ) / 255.0
    )

    # =====================================================
    # 9. GENERATE HEATMAP
    # =====================================================

    heatmap_overlay = generate_gradcam(
        model_wrapper=gradcam_wrapper,
        image_tensor=image_tensor,
        original_rgb_image=original_image,
        target_layer=target_layer,
        target_category=predicted_index
    )

    # =====================================================
    # 10. SAVE HEATMAP
    # =====================================================

    heatmap_filename = f"{uuid.uuid4()}.jpg"

    heatmap_path = (
        HEATMAP_DIR / heatmap_filename
    )

    heatmap_image = Image.fromarray(
        (heatmap_overlay * 255).astype(np.uint8)
    )

    # heatmap_image.save(heatmap_path)
    buffered = io.BytesIO()
    heatmap_image.save(buffered, format="JPEG")
    heatmap_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # =====================================================
    # 11. RESPONSE
    # =====================================================

    return {
    "success": True,
    "predicted_disease": predicted_disease,
    "confidence_score": confidence,
    "heatmap_base64": heatmap_base64, 
    "skin_probability": skin_probability
}