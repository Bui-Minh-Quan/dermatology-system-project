import os
import torch
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from config.database import SessionLocal
from config.ml_state import ml_state
from models.users import AIDiagnosis, DiagnosisStatusEnum

from .ml_engine import (
    generate_gradcam_and_predict,
    TrimodalGradCamWrapper,
    skin_detector_transform,
    disease_classifier_transform,
    DISEASE_CLASSES_9
)

def process_diagnosis_internal(diagnosis_id: str, image_path: str, symptoms: str, body_vector: list):
    """
    Executes natively in the background thread of the main Uvicorn process.
    Accesses the pre-loaded models instantly via ml_state.
    """
    # 1. Create a fresh database session for this background thread
    db: Session = SessionLocal()
    diagnosis = db.query(AIDiagnosis).filter(AIDiagnosis.diagnosis_id == diagnosis_id).first()
    
    if not diagnosis:
        db.close()
        return

    try:
        # Update status to processing
        diagnosis.status = DiagnosisStatusEnum.PROCESSING
        db.commit()

        # Open image 
        raw_image = Image.open(image_path).convert("RGB")
        
        # ==========================================
        # STAGE 1: GATEKEEPER (Skin Detection)
        # ==========================================
        gatekeeper_tensor = skin_detector_transform(raw_image).unsqueeze(0).to(ml_state.device)
        
        with torch.inference_mode():
            # Grab the model directly from global state!
            gate_logits = ml_state.gatekeeper(gatekeeper_tensor)
            is_skin_prob = torch.sigmoid(gate_logits).item()
            
        if is_skin_prob < 0.5:
            diagnosis.status = DiagnosisStatusEnum.REJECTED
            diagnosis.error_message = "Image rejected. Please provide a clear photo of the affected skin."
            db.commit()
            db.close()
            return
            
        # ==========================================
        # STAGE 2: PREPARE TRIMODAL INPUTS
        # ==========================================
        trimodal_tensor = disease_classifier_transform(raw_image).unsqueeze(0).to(ml_state.device)
        meta_tensor = torch.tensor([body_vector], dtype=torch.float32).to(ml_state.device)
        
        symptoms_text = symptoms if symptoms else ""
        
        # Grab the tokenizer from global state!
        encoded_text = ml_state.tokenizer(
            [symptoms_text], 
            padding='max_length', 
            truncation=True, 
            max_length=64, 
            return_tensors='pt'
        ).to(ml_state.device)
        
        has_text_mask = torch.tensor([[1.0 if symptoms else 0.0]], dtype=torch.float32).to(ml_state.device)

        # ==========================================
        # STAGE 3A: PASS 1 - FULL TRIMODAL PREDICTION
        # ==========================================
        with torch.inference_mode():
            logits = ml_state.trimodal_classifier(
                image=trimodal_tensor,
                location_vector=meta_tensor,
                input_ids=encoded_text['input_ids'],
                attention_mask=encoded_text['attention_mask'],
                has_text_mask=has_text_mask
            )
            
            confidence = torch.softmax(logits, dim=1).max().item()
            predicted_idx = torch.argmax(logits, dim=1).item()
            predicted_disease = DISEASE_CLASSES_9[predicted_idx]

        # ==========================================
        # STAGE 3B: PASS 2 - UNIMODAL GRAD-CAM 
        # ==========================================
        # We drop the text and metadata so gradients flow 100% to the image
        empty_text_mask = torch.tensor([[0.0]], dtype=torch.float32).to(ml_state.device)
        
        wrapper_model = TrimodalGradCamWrapper(
            model=ml_state.trimodal_classifier,
            location_vector=None,             # Drops the metadata branch
            input_ids=encoded_text['input_ids'], 
            attention_mask=encoded_text['attention_mask'],
            has_text_mask=empty_text_mask     # Drops the text branch
        )
        
        target_layer = wrapper_model.model.image_encoder.features[7]
        
        # We pass the predicted_idx from Pass 1 so Grad-CAM explains the exact disease
        heatmap_overlay, _ = generate_gradcam_and_predict(
            model_wrapper=wrapper_model, 
            image_tensor=trimodal_tensor, 
            original_rgb_image=np.array(raw_image.resize((384, 384))) / 255.0, 
            target_layer=target_layer,
            threshold=0.2,
            target_category=predicted_idx  
        )
        
        # ==========================================
        # STAGE 4: SAVE OUTPUTS & FINALIZE
        # ==========================================
        heatmap_filename = f"heatmap_{diagnosis_id}.jpg"
        heatmap_path = os.path.join("static", "heatmaps", heatmap_filename) 
        
        heatmap_image = Image.fromarray((heatmap_overlay * 255).astype(np.uint8))
        heatmap_image.save(heatmap_path)

        diagnosis.predicted_disease = predicted_disease
        diagnosis.confidence_score = confidence
        diagnosis.heatmap_url = f"/static/heatmaps/{heatmap_filename}"
        diagnosis.status = DiagnosisStatusEnum.COMPLETED
        db.commit()

    except Exception as e:
        diagnosis.status = DiagnosisStatusEnum.FAILED
        diagnosis.error_message = f"Inference Error: {str(e)}"
        db.commit()
    finally:
        db.close()