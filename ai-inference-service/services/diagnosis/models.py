import torch 
import torch.nn as nn

from torchvision.models import (
    mobilenet_v3_small,
    efficientnet_v2_s
)

from transformers import AutoModel 


# =========================================================
# GATEKEEPER MODEL
# =========================================================
class Gatekeeper(nn.Module):

    def __init__(self):
        super().__init__()

        model = mobilenet_v3_small(weights=None)

        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, 1)

        self.features = model.features
        self.avgpool = model.avgpool
        self.classifier = model.classifier

    def forward(self, x):

        x = self.features(x)

        x = self.avgpool(x)

        x = x.mean([2, 3])

        x = self.classifier(x)

        return x
    

# =========================================================
# DISEASE CLASSIFIER
# =========================================================
class DiseaseClassifier(nn.Module):
    def __init__(
        self, 
        num_classes=9, 
        metadata_dim=8,
        shared_dim=256,
        dropout=0.3,
        text_model_name="vinai/phobert-base-v2"
    ):
        
        super().__init__()

        # =====================================================
        # IMAGE ENCODER
        # =====================================================
        self.image_encoder = efficientnet_v2_s(weights=None)
        image_feature_dim = (self.image_encoder.classifier[-1].in_features)

        # Remove original classifier
        self.image_encoder.classifier = nn.Identity()

        # =====================================================
        # IMAGE PROJECTION
        # =====================================================
        self.img_proj = nn.Sequential(
            nn.Linear(image_feature_dim, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, shared_dim)
        )

        # =====================================================
        # METADATA ENCODER
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
        # TEXT ENCODER
        # =====================================================
        self.text_encoder = AutoModel.from_pretrained(text_model_name)

        self.text_proj = nn.Sequential(
            nn.Linear(768, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, shared_dim)
        )

        # =====================================================
        # MODALITY EMBEDDINGS
        # =====================================================
        self.modality_embeddings = nn.Parameter(torch.randn(3, shared_dim))

        # =====================================================
        # MULTIMODAL TRANSFORMER
        # =====================================================
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=shared_dim,
            nhead=8,
            dim_feedforward=512,
            dropout=dropout,
            activation="gelu",
            batch_first=True
        )

        self.fusion_transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)

        # =====================================================
        # ATTENTION POOLING
        # =====================================================
        self.attention_pool = nn.Sequential(
            nn.Linear(shared_dim, 1)
        )

        # =====================================================
        # FINAL CLASSIFIER
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
        # IMAGE FEATURES
        # =====================================================
        image_features = self.image_encoder(image)
        image_features = self.img_proj(image_features)
        image_features = image_features.unsqueeze(1)


        # =====================================================
        # METADATA FEATURES
        # =====================================================
        if location_vector is not None:
            metadata_features = self.meta_encoder(location_vector)
        else:
            metadata_features = torch.zeros(batch_size, 256, device=device)

        metadata_features = metadata_features.unsqueeze(1)

        # =====================================================
        # TEXT FEATURES
        # =====================================================
        if input_ids is not None:
            text_outputs = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
            cls_embedding = (text_outputs.last_hidden_state[:, 0])
            text_features = self.text_proj(cls_embedding)

            if has_text_mask is not None:
                text_features = (text_features * has_text_mask)
        else:
            text_features = torch.zeros(batch_size, 256, device=device)

        text_features = text_features.unsqueeze(1)

        # =====================================================
        # MULTIMODAL FUSION
        # =====================================================
        multimodal_sequence = torch.cat([image_features, metadata_features, text_features], dim=1)

        multimodal_sequence = (multimodal_sequence + self.modality_embeddings.unsqueeze(0))
        
        fused_sequence = self.fusion_transformer(multimodal_sequence)

        # =====================================================
        # ATTENTION POOLING
        # =====================================================
        attention_scores = self.attention_pool(fused_sequence)
        attention_weights = torch.softmax(attention_scores, dim=1)

        fused_embedding = torch.sum(fused_sequence * attention_weights, dim=1)

        # =====================================================
        # CLASSIFICATION
        # =====================================================
        logits = self.classifier(fused_embedding)

        return logits


