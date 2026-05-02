from pydantic import BaseModel 
from uuid import UUID 
from datetime import datetime 
from typing import Optional, List

class DiagnosisResponse(BaseModel):
    diagnosis_id: UUID 
    predicted_disease: str 
    confidence_score: float
    icd10_code: Optional[str] = None
    input_image_url: str 
    heatmap_url: str 
    created_at: datetime

    class Config:
        from_attributes = True