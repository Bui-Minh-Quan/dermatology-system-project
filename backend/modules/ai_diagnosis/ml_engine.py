import os
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from transformers import AutoModel, AutoTokenizer

from PIL import Image

import cv2
import numpy as np
import torch
from pytorch_grad_cam import GradCAMPlusPlus

DISEASE_CLASSES_9 = sorted([
    'Acne Vulgaris',
    'Atopic Dermatitis',
    'Contact Dermatitis',
    'Normal Skin',
    'Psoriasis',
    'Rosacea',
    'Seborrheic Dermatitis',
    'Tinea',
    'Urticaria'
])

skin_detector_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

disease_classifier_transform = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def build_baseline_model(num_classes=10):
    weights = EfficientNet_V2_S_Weights.IMAGENET1K_V1
    model = efficientnet_v2_s(weights=weights)

    # 1. FREEZE the base feature extractor layers
    for param in model.features.parameters():
        param.requires_grad = False

    # 2. Replace the final classification head
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)

    return model


def build_skin_detector():
    # Load lightweight MobileNet
    weights = MobileNet_V3_Small_Weights.DEFAULT 
    model = mobilenet_v3_small(weights=weights)

    # Unfreeze the last few layers for slight fine-tuning
    for param in model.features[:-4].parameters():
        param.requires_grad = False
    
    # Replace classifier for Binary Output (1 = Skin, 0 = Garbage/Object)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, 1)

    return model

class ProductionTrimodalModel(nn.Module):

    def __init__(
        self,
        num_classes=9,
        metadata_dim=8,
        shared_dim=256,
        text_model_name="vinai/phobert-base-v2",
        dropout=0.3
    ):
        super(ProductionTrimodalModel, self).__init__()

        # =====================================================
        # 1. IMAGE BRANCH
        # =====================================================

        # EfficientNet backbone
        self.image_encoder = build_baseline_model(num_classes=10)

        # Remove classification head
        self.image_encoder.classifier = nn.Identity()

        # Freeze lower CNN layers
        for name, param in self.image_encoder.features.named_parameters():

            # Fine-tune only high-level blocks
            if name.startswith("6") or name.startswith("7"):
                param.requires_grad = True
            else:
                param.requires_grad = False

        # Image projection
        self.img_proj = nn.Sequential(
            nn.Linear(1280, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, shared_dim)
        )

        # =====================================================
        # 2. METADATA BRANCH
        # =====================================================

        self.meta_encoder = nn.Sequential(
            nn.Linear(metadata_dim, 64),
            nn.ReLU(),

            nn.Linear(64, 128),
            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(128, shared_dim)
        )

        # =====================================================
        # 3. TEXT BRANCH
        # =====================================================

        self.text_encoder = AutoModel.from_pretrained(
            text_model_name
        )

        # Freeze language model
        for param in self.text_encoder.parameters():
            param.requires_grad = False

        self.text_proj = nn.Sequential(
            nn.Linear(768, 512),
            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(512, shared_dim)
        )

        # =====================================================
        # 4. MODALITY EMBEDDINGS
        # =====================================================
        # Learnable embeddings to distinguish modalities
        self.modality_embeddings = nn.Parameter(
            torch.randn(3, shared_dim)
        )

        # =====================================================
        # 5. TRANSFORMER FUSION
        # =====================================================
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=shared_dim,
            nhead=8,
            dim_feedforward=512,
            dropout=dropout,
            batch_first=True,
            activation="gelu"
        )

        self.fusion_transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2
        )

        # =====================================================
        # 6. ATTENTION POOLING
        # =====================================================

        self.attention_pool = nn.Sequential(
            nn.Linear(shared_dim, 1)
        )

        # =====================================================
        # 7. FINAL CLASSIFIER
        # =====================================================

        self.classifier = nn.Sequential(

            nn.Linear(shared_dim, 256),

            nn.BatchNorm1d(256),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(256, 128),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(128, num_classes)
        )

    # =========================================================
    # FORWARD
    # =========================================================

    def forward(
        self,
        image,
        location_vector=None,
        input_ids=None,
        attention_mask=None,
        has_text_mask=None
    ):

        batch_size = image.size(0)
        device = image.device

        # =====================================================
        # 1. IMAGE FEATURES
        # =====================================================

        img_feat = self.image_encoder(image)

        img_feat = self.img_proj(img_feat)

        img_feat = img_feat.unsqueeze(1)

        # Shape:
        # [Batch, 1, 256]

        # =====================================================
        # 2. METADATA FEATURES
        # =====================================================

        if location_vector is not None:

            meta_feat = self.meta_encoder(location_vector)

        else:
            meta_feat = torch.zeros(
                batch_size,
                256,
                device=device
            )

        meta_feat = meta_feat.unsqueeze(1)

        # Shape:
        # [Batch, 1, 256]

        # =====================================================
        # 3. TEXT FEATURES
        # =====================================================

        if input_ids is not None:

            text_outputs = self.text_encoder(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

            # CLS token representation
            text_cls = text_outputs.last_hidden_state[:, 0]

            txt_feat = self.text_proj(text_cls)

            # Handle missing text
            if has_text_mask is not None:

                txt_feat = txt_feat * has_text_mask

        else:

            txt_feat = torch.zeros(
                batch_size,
                256,
                device=device
            )

        txt_feat = txt_feat.unsqueeze(1)

        # Shape:
        # [Batch, 1, 256]

        # =====================================================
        # 4. STACK MODALITIES
        # =====================================================

        multimodal_sequence = torch.cat(
            [
                img_feat,
                meta_feat,
                txt_feat
            ],
            dim=1
        )

        # Shape:
        # [Batch, 3, 256]

        # =====================================================
        # 5. ADD MODALITY EMBEDDINGS
        # =====================================================

        multimodal_sequence = (
            multimodal_sequence +
            self.modality_embeddings.unsqueeze(0)
        )

        # =====================================================
        # 6. CROSS-MODAL TRANSFORMER
        # =====================================================

        fused_sequence = self.fusion_transformer(
            multimodal_sequence
        )

        # Shape:
        # [Batch, 3, 256]

        # =====================================================
        # 7. ATTENTION POOLING
        # =====================================================

        attention_scores = self.attention_pool(
            fused_sequence
        )

        # Shape:
        # [Batch, 3, 1]

        attention_weights = torch.softmax(
            attention_scores,
            dim=1
        )

        fused_embedding = torch.sum(
            fused_sequence * attention_weights,
            dim=1
        )

        # Shape:
        # [Batch, 256]

        # =====================================================
        # 8. CLASSIFICATION
        # =====================================================

        logits = self.classifier(
            fused_embedding
        )

        return logits

# =========================================================
# GRAD-CAM IMPLEMENTATION
# =========================================================

class TrimodalGradCamWrapper(nn.Module):
    """
    Wraps the Trimodal model so Grad-CAM only sees the image input.
    Optimized to cache logits during the Grad-CAM forward pass to prevent redundant calculations.
    """
    def __init__(self, model, location_vector, input_ids, attention_mask, has_text_mask):
        super().__init__()
        self.model = model
        self.location_vector = location_vector
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.has_text_mask = has_text_mask
        self.last_logits = None  # Cache for the forward pass

    def forward(self, image_tensor):
        logits = self.model(
            image=image_tensor,
            location_vector=self.location_vector,
            input_ids=self.input_ids,
            attention_mask=self.attention_mask,
            has_text_mask=self.has_text_mask
        )
        self.last_logits = logits  # Save the logits before returning!
        return logits


def generate_gradcam_and_predict(model_wrapper, image_tensor, original_rgb_image, target_layer, threshold=0.4, target_category=None):
    """
    Generates the Grad-CAM overlay. Accepts a target_category to force Grad-CAM 
    to explain a specific disease prediction.
    """
    model_wrapper.eval()
    image_tensor.requires_grad_(True)

    # Force Grad-CAM to look at a specific class index if provided
    targets = [ClassifierOutputTarget(target_category)] if target_category is not None else None

    with GradCAMPlusPlus(model=model_wrapper, target_layers=[target_layer]) as cam:
        grayscale_cam = cam(input_tensor=image_tensor, targets=targets)[0]

    logits = model_wrapper.last_logits

    # Resize, Threshold, and Blend
    resized_cam = cv2.resize(
        grayscale_cam, 
        (original_rgb_image.shape[1], original_rgb_image.shape[0])
    )
    resized_cam[resized_cam < threshold] = 0.0

    heatmap = cv2.applyColorMap(np.uint8(255 * resized_cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB) / 255.0

    alpha = resized_cam[:, :, np.newaxis] * 0.6 
    visualization = (heatmap * alpha) + (original_rgb_image * (1 - alpha))
    visualization = np.clip(visualization, 0, 1)

    return visualization, logits




print("✅ Baseline trimodal model defined successfully!")