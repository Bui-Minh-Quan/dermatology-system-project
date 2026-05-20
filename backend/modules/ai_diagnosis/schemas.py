from pydantic import BaseModel 
from uuid import UUID 
from datetime import datetime 
from typing import Optional

class DiagnosisResponse(BaseModel):
    diagnosis_id: UUID 
    status: str  # Add the status field!
    input_image_url: str 
    created_at: datetime
    
    # Make these Optional since they won't exist immediately
    predicted_disease: Optional[str] = None
    confidence_score: Optional[float] = None
    icd10_code: Optional[str] = None
    heatmap_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True