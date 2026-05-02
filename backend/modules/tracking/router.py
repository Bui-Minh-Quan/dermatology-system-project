import os
import shutil
import random
from fastapi import UploadFile, File
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from models.users import User, RoleEnum, TrackingSession, TrackingStatusEnum, TrackingLog
from modules.auth.security import get_current_user
from . import schemas
from uuid import UUID
import uuid
from typing import List

# Directory to store tracking session images
TRACKING_IMAGE_DIR = "static/tracking_images"
os.makedirs(TRACKING_IMAGE_DIR, exist_ok=True)


router = APIRouter(prefix="/tracking/sessions", tags=["Tracking Sessions"])

# Create a new tracking session
@router.post("/", response_model=schemas.SessionResponse, status_code=status.HTTP_201_CREATED)
def create_tracking_session(
    session_in: schemas.SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can create tracking sessions")
    
    new_session = TrackingSession(
        patient_id=current_user.user_id,
        session_name=session_in.session_name,
        target_disease=session_in.target_disease,
        status=TrackingStatusEnum.ACTIVE
    )

    try:
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create tracking session")
    

# Get all tracking sessions for the current patient
@router.get("/", response_model=List[schemas.SessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can view their tracking sessions")
    
    sessions = db.query(TrackingSession).filter(
        TrackingSession.patient_id == current_user.user_id
    ).all()

    return sessions

# Update tracking session status/name
@router.patch("/{session_id}", response_model=schemas.SessionResponse)
def update_session(
    session_id: UUID, 
    session_in: schemas.SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only find the session if it belongs to the current user
    session = db.query(TrackingSession).filter(
        TrackingSession.session_id == session_id,
        TrackingSession.patient_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")
    
    # Update only the fields that were provided
    update_data = session_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    
    try:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update tracking session")

# Delete a tracking session
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(TrackingSession).filter(
        TrackingSession.session_id == session_id,
        TrackingSession.patient_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")

    try:
        db.delete(session)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete tracking session")


# Add an image to a tracking session (add log and calculate delta)
@router.post("/{session_id}/logs", response_model=schemas.LogResponse)
async def add_tracking_log(
    session_id: UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Verify session belongs to user
    session = db.query(TrackingSession).filter(
        TrackingSession.session_id == session_id,
        TrackingSession.patient_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")
    
    # 2. Save image to disk
    file_extension = image.filename.split(".")[-1].lower()
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(TRACKING_IMAGE_DIR, file_name)
    web_url = f"/static/tracking_images/{file_name}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # 3. Mock AI logic: get the previous log and calculate a random delta
    previous_log = db.query(TrackingLog).filter(
        TrackingLog.session_id == session_id
    ).order_by(TrackingLog.logged_at.desc()).first()

    delta_area, delta_color, delta_texture = None, None, None

    if previous_log:
        delta_area = round(random.uniform(-10, 10), 2)  # percentage change
        delta_color = round(random.uniform(-5, 5), 2)    # color score change
        delta_texture = round(random.uniform(-5, 5), 2)  # texture score change
    
    # 4. Create log entry
    new_log = TrackingLog(
        session_id=session_id,
        image_url=web_url,
        delta_area=delta_area,
        delta_color=delta_color,
        delta_texture=delta_texture
    )

    try:
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except Exception as e:
        db.rollback()
        # Cleanup the saved image if DB operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to add tracking log")


# Get all logs for a tracking session
@router.get("/{session_id}/logs", response_model=List[schemas.LogResponse])
def get_tracking_logs(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    # Verify session belongs to user
    session = db.query(TrackingSession).filter(
        TrackingSession.session_id == session_id,
        TrackingSession.patient_id == current_user.user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")
    
    # Get logs sorted by logged_at ascending
    logs = db.query(TrackingLog).filter(
        TrackingLog.session_id == session_id
    ).order_by(TrackingLog.logged_at.asc()).all()

    return logs
