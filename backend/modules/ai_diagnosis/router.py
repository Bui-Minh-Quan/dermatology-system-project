import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from config.queue import diagnosis_queue  # Importing the RQ queue (though we will not use it in this version)

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status # Added for native background processing
)
from sqlalchemy.orm import Session

# Import database and models
from config.database import get_db 
from models.users import User, AIDiagnosis, DiagnosisStatusEnum
from modules.auth.security import get_current_user
from . import schemas

# Import the inference function
from .inference import process_diagnosis_internal

load_dotenv()

router = APIRouter(
    prefix="/diagnosis",
    tags=["AI Diagnosis"]
)

# =========================================================
# CONFIG SETUP (Redis removed)
# =========================================================
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "static/uploads"))
HEATMAP_DIR = Path(os.getenv("HEATMAP_DIR", "static/heatmaps"))

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))  # 5MB default

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
HEATMAP_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# HELPERS
# =========================================================
def validate_image(image: UploadFile):
    """Validates the uploaded file's type and extension."""
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    file_extension = image.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return file_extension


# =========================================================
# ENDPOINTS
# =========================================================
@router.post("/", response_model=schemas.DiagnosisResponse)
async def create_diagnosis(
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(None),
    body_vector: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads an image, creates a PENDING database record, 
    and triggers the AI Inference natively in the background.
    """
    # 1. Validate Image
    file_extension = validate_image(image)

    # 2. Save Image Locally
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image to disk: {str(e)}"
        )
    
    image_url = f"/static/uploads/{unique_filename}"

    # 3. Parse metadata vector 
    try:
        vector_list = [int(x.strip()) for x in body_vector.split(",")] if body_vector else [0]*8
        if len(vector_list) != 8:
            vector_list = [0]*8  # Fallback if malformed
    except ValueError:
        vector_list = [0]*8

    # 4. Database Transaction & Queueing
    try:
        # Create PENDING record
        diagnosis = AIDiagnosis(
            patient_id=current_user.user_id,
            input_image_url=image_url,
            input_symptoms=symptoms,
            input_body_vector=vector_list,
            status=DiagnosisStatusEnum.PENDING
        )

        db.add(diagnosis)
        db.commit()
        db.refresh(diagnosis)

        # FIRE THE BACKGROUND TASK NATIVELY
        diagnosis_queue.enqueue(
            process_diagnosis_internal,
            str(diagnosis.diagnosis_id),
            str(file_path),
            symptoms,
            vector_list
        )

        return diagnosis
    
    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()  # Clean up orphaned image
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue AI Diagnosis: {str(e)}"
        )
    

@router.get("/{diagnosis_id}", response_model=schemas.DiagnosisResponse)
def get_diagnosis_status(
    diagnosis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the current status of a diagnosis. 
    The frontend should poll this endpoint until status is COMPLETED or FAILED.
    """
    diagnosis = db.query(AIDiagnosis).filter(
        AIDiagnosis.diagnosis_id == diagnosis_id,
        AIDiagnosis.patient_id == current_user.user_id
    ).first()

    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis record not found or access denied."
        )
    
    return diagnosis