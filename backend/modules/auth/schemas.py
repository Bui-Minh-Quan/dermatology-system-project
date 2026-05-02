from pydantic import BaseModel, EmailStr, Field, field_validator
from models.users import RoleEnum, UserStatusEnum
from uuid import UUID
from datetime import datetime
from typing import Optional
import re

class Token(BaseModel):
    access_token: str
    token_type: str
    role: RoleEnum         
    status: UserStatusEnum   

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email_phone: str 
    password: str 

class OTPRequest(BaseModel):
    email_phone: str 

class BaseRegister(BaseModel):
    email_phone: EmailStr 
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str 
    date_of_birth: datetime
    gender: str 
    otp_code: str 

    @field_validator("password")
    def validate_password(cls, v):
        # Requires at least one number and one letter
        if not re.search(r"\d", v) or not re.search(r"[a-zA-Z]", v):
            raise ValueError('Password must contain at least one letter and one number')
        return v


class PatientRegister(BaseRegister):
    address: Optional[str] = None 
    # Role is automatically assumed to be PATIENT in the router

class DoctorRegister(BaseRegister):
    license_number: str 
    specialty: str 
    workplace: str 
    avatar_url: Optional[str] = None 
    degree_image_url: str 
