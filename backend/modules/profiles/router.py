from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy.orm import Session 
from config.database import get_db
from models.users import User, RoleEnum
from .schemas import PatientProfileUpdate, DoctorProfileUpdate, DoctorProfileResponse

from modules.auth.security import get_current_user
from . import schemas

router = APIRouter(prefix="/profiles", tags=["Profiles"])

USER_IDENTITY_FIELDS = ["full_name", "date_of_birth", "gender", "avatar_url"]

@router.put("/patient")
def update_patient_profile(
    update_data: schemas.PatientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Not authorized to update patient profile")
    
    profile = current_user.patient_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # 🚦 Traffic Controller: Route data to the correct table
    for key, value in update_dict.items():
        if key in USER_IDENTITY_FIELDS:
            setattr(current_user, key, value) # Update User table
        else:
            setattr(profile, key, value)      # Update PatientProfile table
    
    try: 
        db.commit()
        db.refresh(current_user)
        db.refresh(profile)
        
        # Merge data for the response
        return {
            "message": "Patient profile updated successfully", 
            "profile": {
                "full_name": current_user.full_name,
                "address": profile.address,
                "avatar_url": current_user.avatar_url
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update patient profile")



@router.patch("/doctor", response_model=schemas.DoctorProfileResponse)
def update_doctor_profile(
    update_data: schemas.DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Not authorized to update doctor profile")

    profile = current_user.doctor_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    
    # 🚦 Traffic Controller: Route data to the correct table
    for key, value in update_dict.items():
        if key in USER_IDENTITY_FIELDS:
            setattr(current_user, key, value) # Update User table
        else:
            setattr(profile, key, value)      # Update DoctorProfile table
    
    try:
        db.commit()
        db.refresh(current_user)
        db.refresh(profile)
        
        # Merge data from BOTH tables to satisfy the DoctorProfileResponse schema
        return {
            "doctor_id": str(profile.doctor_id),
            "full_name": current_user.full_name,
            "date_of_birth": current_user.date_of_birth,
            "gender": current_user.gender,
            "avatar_url": current_user.avatar_url,
            "license_number": profile.license_number,
            "specialty": profile.specialty,
            "workplace": profile.workplace,
            "experience_years": profile.experience_years,
            "bio": profile.bio,
            "degree_image_url": profile.degree_image_url,
            "rating_average": profile.rating_average
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update doctor profile")