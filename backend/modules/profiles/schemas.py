from pydantic import BaseModel
from typing import Optional 
from datetime import datetime

# Schema for patient
class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None 
    date_of_birth: Optional[datetime] = None 
    gender: Optional[str] = None 
    address: Optional[str] = None 
    avatar_url: Optional[str] = None 

# Schema for doctor
class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    experience_years: Optional[int] = None
    bio: Optional[str] = None
    workplace: Optional[str] = None
    specialty: Optional[str] = None

class DoctorProfileResponse(BaseModel):
    doctor_id: str
    full_name: str
    date_of_birth: datetime
    gender: str
    license_number: str
    specialty: str
    workplace: str
    experience_years: Optional[int] 
    bio: Optional[str] 
    avatar_url: Optional[str] 
    degree_image_url: str
    rating_average: float

    class Config:
        from_attributes = True
