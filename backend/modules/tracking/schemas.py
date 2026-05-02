from pydantic import BaseModel 
from typing import Optional
from uuid import UUID 
from models.users import TrackingStatusEnum
from datetime import datetime

class SessionCreate(BaseModel):
    session_name: str 
    target_disease: Optional[str] = None

class SessionUpdate(BaseModel):
    session_name: Optional[str] = None 
    target_disease: Optional[str] = None
    status: Optional[TrackingStatusEnum] = None

class SessionResponse(BaseModel):
    session_id: UUID 
    patient_id: UUID
    session_name: str 
    target_disease: Optional[str] = None
    status: TrackingStatusEnum

    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    log_id: UUID
    session_id: UUID
    image_url: str
    delta_area: Optional[float] = None
    delta_color: Optional[float] = None
    delta_texture: Optional[float] = None
    doctor_notes: Optional[str] = None
    logged_at: datetime

    class Config:
        from_attributes = True

