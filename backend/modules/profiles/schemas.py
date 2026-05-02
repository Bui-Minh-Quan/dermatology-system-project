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
    specialty: Optional[str] = None 
    workplace: Optional[str] = None 
    experience_years: Optional[int] = None 
    bio: Optional[str] = None 
    avatar_url: Optional[str] = None 
