from pydantic import BaseModel 
from typing import List, Optional
from uuid import UUID

class RecommendationRequest(BaseModel):
    symptoms: Optional[str] = None 
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    diagnosis_id: Optional[UUID] = None

class DoctorRecommendation(BaseModel):
    doctor_id: UUID
    full_name: str
    specialty: str
    workplace: str 
    rating_average: float
    distance_km: Optional[float] = None 
    avatar_url: Optional[str] = None   
    is_online: bool = False 

    class Config:
        from_attributes = True