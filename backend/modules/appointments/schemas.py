from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from models.users import AppointmentStatusEnum

class AppointmentCreate(BaseModel):
    doctor_id: UUID
    appointment_time: datetime

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatusEnum
    reason_for_cancellation: Optional[str] = None
    meeting_notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    appointment_id: UUID
    patient_name: str
    doctor_name: str
    specialty: str
    workplace: str
    appointment_time: datetime
    status: AppointmentStatusEnum

    class Config:
        from_attributes = True
        