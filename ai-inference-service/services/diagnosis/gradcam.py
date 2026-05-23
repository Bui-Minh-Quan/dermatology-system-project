import cv2 
import numpy as np
import torch 
import torch.nn as nn

from pytorch_grad_cam import GradCAMPlusPlus 
from pytorch_grad_cam.utils.model_targets import (
    ClassifierOutputTarget 
)


# =========================================================
# WRAPPER
# =========================================================
class GradCAMWrapper(nn.Module):
    """
    Wraps the multimodal classifier so GradCAM
    only receives image tensors as input.
    """
    def __init__(self, model, location_vector, input_ids, attention_mask, has_text_mask):
        super().__init__()

        self.model = model
        self.location_vector = location_vector
        self.input_ids = input_ids
        self.attention_mask = attention_mask
        self.has_text_mask = has_text_mask

        self.cached_logits = None

    def forward(self, image_tensor):

        logits = self.model(
            image=image_tensor,
            location_vector=self.location_vector,
            input_ids=self.input_ids,
            attention_mask=self.attention_mask,
            has_text_mask=self.has_text_mask
        )

        self.cached_logits = logits

        return logits
    
# =========================================================
# GENERATE GRADCAM
# =========================================================
def generate_gradcam(
    model_wrapper,
    image_tensor,
    original_rgb_image,
    target_layer,
    target_category,
    threshold=0.2
):
    """
    Generates GradCAM++ visualization.
    """
    model_wrapper.eval()

    image_tensor.requires_grad_(True)

    targets = [
        ClassifierOutputTarget(target_category)
    ]

    with GradCAMPlusPlus(
        model=model_wrapper,
        target_layers=[target_layer]
    ) as cam:
        grayscale_cam = cam(
            input_tensor=image_tensor,
            targets=targets
        )[0]

    # =====================================================
    # RESIZE CAM
    # =====================================================
    resized_cam = cv2.resize(
        grayscale_cam,
        (
            original_rgb_image.shape[1],
            original_rgb_image.shape[0]
        )
    )

    # =====================================================
    # THRESHOLD
    # =====================================================
    resized_cam[resized_cam < threshold] = 0.0

    # =====================================================
    # COLORMAP
    # =====================================================
    heatmap = cv2.applyColorMap(np.uint8(255 * resized_cam), cv2.COLORMAP_JET)

    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB) / 255.0

    # =====================================================
    # BLEND
    # =====================================================
    alpha = resized_cam[:, :, np.newaxis] * 0.6
    visualization = (heatmap * alpha + original_rgb_image * (1 - alpha))

    visualization = np.clip(visualization, 0, 1)

    return visualization
