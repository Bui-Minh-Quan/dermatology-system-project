import base64
import os
from urllib import response
import uuid
import shutil
import json
from pathlib import Path
from typing import Optional
import traceback

import httpx
from dotenv import load_dotenv
from PIL import Image

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status
)

from sqlalchemy.orm import Session

# =========================================================
# DATABASE + MODELS
# =========================================================
from config.database import get_db
from models.users import (
    User,
    AIDiagnosis,
    DiagnosisStatusEnum
)

from modules.auth.security import get_current_user
from . import schemas


# =========================================================
# LOAD ENV
# =========================================================
load_dotenv()


# =========================================================
# ROUTER
# =========================================================
router = APIRouter(
    prefix="/diagnosis",
    tags=["AI Diagnosis"]
)


# =========================================================
# CONFIG
# =========================================================
UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        "static/uploads"
    )
)

HEATMAP_DIR = Path(
    os.getenv(
        "HEATMAP_DIR",
        "static/heatmaps"
    )
)

MAX_FILE_SIZE = int(
    os.getenv(
        "MAX_FILE_SIZE",
        5 * 1024 * 1024
    )
)

AI_INFERENCE_URL = os.getenv(
    "AI_INFERENCE_URL",
    "http://localhost:8001"
)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

HEATMAP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# =========================================================
# HELPERS
# =========================================================
def validate_image(image: UploadFile):

    # -----------------------------------------------------
    # CHECK FILENAME
    # -----------------------------------------------------
    if not image.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename"
        )

    # -----------------------------------------------------
    # MIME TYPE VALIDATION
    # -----------------------------------------------------
    if image.content_type not in ALLOWED_MIME_TYPES:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid file type. "
                f"Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
            )
        )

    # -----------------------------------------------------
    # EXTENSION VALIDATION
    # -----------------------------------------------------
    file_extension = (
        image.filename
        .split(".")[-1]
        .lower()
    )

    if file_extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid file extension. "
                f"Allowed extensions: "
                f"{', '.join(ALLOWED_EXTENSIONS)}"
            )
        )

    # -----------------------------------------------------
    # FILE SIZE VALIDATION
    # -----------------------------------------------------
    image.file.seek(0, 2)
    file_size = image.file.tell()
    image.file.seek(0)

    if file_size > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File too large. "
                f"Maximum allowed size: "
                f"{MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        )

    return file_extension


def parse_body_vector(raw_value: str):

    try:

        cleaned = (
            raw_value
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
        )

        values = cleaned.split(",")

        vector = [float(x) for x in values]

        # Check if vector has only binary values (0 or 1)
        if not all(x in (0.0, 1.0) for x in vector):
            raise ValueError()

        if len(vector) != 8:
            raise ValueError()

        return vector

    except Exception:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid body_vector format. "
                "Expected: [1,0,0,0,0,0,0,0]"
            )
        )



def verify_actual_image(file_path: Path):

    """
    Verify uploaded file is truly an image.
    """

    try:

        with Image.open(file_path) as img:
            img.verify()

    except Exception:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupted image file"
        )


# Helper for error handling and status updates
def update_diagnosis_status(db: Session, diagnosis: AIDiagnosis, status: DiagnosisStatusEnum, error: str = None):
    diagnosis.status = status
    diagnosis.error_message = error
    db.commit()


# =========================================================
# CREATE DIAGNOSIS
# =========================================================
@router.post("/", response_model=schemas.DiagnosisResponse)
async def create_diagnosis(
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(None),
    body_vector: Optional[str] = Form(default="[0,0,0,0,0,0,0,0]"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Initilize diagnosis record with status=PROCESSING
    file_ext = validate_image(image)
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    verify_actual_image(file_path)

    diagnosis = AIDiagnosis(
        patient_id=current_user.user_id,
        input_image_url=f"/static/uploads/{unique_filename}",
        input_symptoms=symptoms,
        input_body_vector=parse_body_vector(body_vector),
        status=DiagnosisStatusEnum.PROCESSING
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    # 2. Call AI inference service
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as img_file:
                response = await client.post(
                    f"{AI_INFERENCE_URL}/diagnosis/infer",
                    files={"image": (unique_filename, img_file, image.content_type)},
                    data={"symptoms": symptoms or "", "body_vector": json.dumps(diagnosis.input_body_vector)}
                )
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        update_diagnosis_status(db, diagnosis, DiagnosisStatusEnum.FAILED, str(e))
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")

    # 3. Process AI results and update diagnosis record
    try:
        heatmap_filename = f"{uuid.uuid4()}.jpg"
        with open(HEATMAP_DIR / heatmap_filename, "wb") as fh:
            fh.write(base64.b64decode(result["heatmap_base64"]))
        
        diagnosis.predicted_disease = result["predicted_disease"]
        diagnosis.confidence_score = result["confidence_score"]
        diagnosis.heatmap_url = f"/static/heatmaps/{heatmap_filename}"
        diagnosis.status = DiagnosisStatusEnum.COMPLETED
        
        db.commit()
        return diagnosis
    except KeyError as e:
        update_diagnosis_status(db, diagnosis, DiagnosisStatusEnum.FAILED, f"Missing field: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid AI response: {e}")
    except Exception as e:
        update_diagnosis_status(db, diagnosis, DiagnosisStatusEnum.FAILED, str(e))
        raise HTTPException(status_code=500, detail="Error processing AI results")

# =========================================================
# GET DIAGNOSIS
# =========================================================
@router.get("/{diagnosis_id}", response_model=schemas.DiagnosisResponse)

def get_diagnosis_status(diagnosis_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    diagnosis = (
        db.query(AIDiagnosis).filter(
            AIDiagnosis.diagnosis_id == diagnosis_id,
            AIDiagnosis.patient_id == current_user.user_id
        ).first()
    )

    if not diagnosis:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=("Diagnosis record not found or access denied."))

    return diagnosis