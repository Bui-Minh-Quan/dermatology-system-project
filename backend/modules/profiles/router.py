from fastapi import APIRouter, Depends, HTTPException, status 
from sqlalchemy.orm import Session 
from config.database import get_db
from models.users import User, RoleEnum 

from modules.auth.security import get_current_user
from . import schemas

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.put("/patient")
def update_patient_profile(
    update_data: schemas.PatientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify role 
    if current_user.role != RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Not authorized to update patient profile")
    
    # 2. Get the profile 
    profile = current_user.patient_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    
    # 3. Update only the fields that were provided
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value) 
    
    # 4. Save and return 
    try: 
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return {"message": "Patient profile updated successfully", "profile": profile}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update patient profile")
    

@router.put("/doctor")
def update_doctor_profile(
    update_data: schemas.DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify Role 
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Not authorized to update doctor profile")

    # 2. Get the profile 
    profile = current_user.doctor_profile
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    # 3. Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)
    
    # 4. Save and return
    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return {"message": "Doctor profile updated successfully", "profile": profile}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update doctor profile")

