import os
import uuid
import shutil
import json
from pathlib import Path
from typing import Optional

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


# =========================================================
# CREATE DIAGNOSIS
# =========================================================
@router.post(
    "/",
    response_model=schemas.DiagnosisResponse
)

async def create_diagnosis(
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(None),
    body_vector: Optional[str] = Form(default="[0,0,0,0,0,0,0,0]"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # PARSE BODY VECTOR
    # -----------------------------------------------------
    parsed_body_vector = parse_body_vector(body_vector)

    # -----------------------------------------------------
    # VALIDATE IMAGE
    # -----------------------------------------------------
    file_extension = validate_image(image)

    # -----------------------------------------------------
    # GENERATE UNIQUE FILE NAME
    # -----------------------------------------------------
    unique_filename = (
        f"{uuid.uuid4()}.{file_extension}"
    )

    file_path = UPLOAD_DIR / unique_filename

    # -----------------------------------------------------
    # SAVE IMAGE
    # -----------------------------------------------------
    try:

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                image.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )

    # -----------------------------------------------------
    # VERIFY ACTUAL IMAGE CONTENT
    # -----------------------------------------------------
    verify_actual_image(file_path)

    # -----------------------------------------------------
    # IMAGE URL
    # -----------------------------------------------------
    image_url = (
        f"/static/uploads/{unique_filename}"
    )

    # -----------------------------------------------------
    # CREATE DATABASE RECORD
    # -----------------------------------------------------
    diagnosis = AIDiagnosis(
        patient_id=current_user.user_id,
        input_image_url=image_url,
        input_symptoms=symptoms,
        input_body_vector=parsed_body_vector,
        status=DiagnosisStatusEnum.PROCESSING
    )

    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    # -----------------------------------------------------
    # CALL AI INFERENCE SERVICE
    # -----------------------------------------------------
    try:

        async with httpx.AsyncClient(
            timeout=60.0
        ) as client:

            with open(file_path, "rb") as img_file:

                response = await client.post(
                    f"{AI_INFERENCE_URL}/diagnosis/infer",

                    files={
                        "image": (
                            unique_filename,
                            img_file,
                            image.content_type
                        )
                    },

                    data={
                        "symptoms": symptoms or "",

                        # SEND SANITIZED VECTOR
                        "body_vector": json.dumps(
                            parsed_body_vector
                        )
                    }
                )

        # -------------------------------------------------
        # AI SERVICE ERROR
        # -------------------------------------------------
        if response.status_code != 200:

            diagnosis.status = (
                DiagnosisStatusEnum.FAILED
            )

            diagnosis.error_message = (
                response.text
            )

            db.commit()

            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        # -------------------------------------------------
        # PARSE JSON RESPONSE
        # -------------------------------------------------
        try:

            result = response.json()

        except Exception:

            diagnosis.status = (
                DiagnosisStatusEnum.FAILED
            )

            diagnosis.error_message = (
                "Invalid JSON response from AI service"
            )

            db.commit()

            raise HTTPException(
                status_code=500,
                detail="Invalid AI response"
            )

        # -------------------------------------------------
        # VALIDATE REQUIRED FIELDS
        # -------------------------------------------------
        required_fields = [
            "predicted_disease",
            "confidence_score",
            "heatmap_path"
        ]

        for field in required_fields:

            if field not in result:

                diagnosis.status = (
                    DiagnosisStatusEnum.FAILED
                )

                diagnosis.error_message = (
                    f"Missing field: {field}"
                )

                db.commit()

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Missing AI response field: {field}"
                    )
                )

    # -----------------------------------------------------
    # HTTPX NETWORK ERRORS
    # -----------------------------------------------------
    except httpx.TimeoutException:

        diagnosis.status = (
            DiagnosisStatusEnum.FAILED
        )

        diagnosis.error_message = (
            "AI service timeout"
        )

        db.commit()

        raise HTTPException(
            status_code=504,
            detail="AI inference timeout"
        )

    except httpx.RequestError as e:

        diagnosis.status = (
            DiagnosisStatusEnum.FAILED
        )

        diagnosis.error_message = str(e)

        db.commit()

        raise HTTPException(
            status_code=503,
            detail=(
                "AI inference service unavailable"
            )
        )

    except HTTPException:
        raise

    except Exception as e:

        diagnosis.status = (
            DiagnosisStatusEnum.FAILED
        )

        diagnosis.error_message = str(e)

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    # -----------------------------------------------------
    # UPDATE DATABASE WITH RESULT
    # -----------------------------------------------------
    diagnosis.status = (
        DiagnosisStatusEnum.COMPLETED
    )

    diagnosis.predicted_disease = (
        result["predicted_disease"]
    )

    diagnosis.confidence_score = (
        result["confidence_score"]
    )

    diagnosis.heatmap_url = (
        result["heatmap_path"]
    )

    db.commit()
    db.refresh(diagnosis)

    return diagnosis


# =========================================================
# GET DIAGNOSIS
# =========================================================
@router.get(
    "/{diagnosis_id}",
    response_model=schemas.DiagnosisResponse
)

def get_diagnosis_status(
    diagnosis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    diagnosis = (
        db.query(AIDiagnosis)
        .filter(
            AIDiagnosis.diagnosis_id == diagnosis_id,
            AIDiagnosis.patient_id == current_user.user_id
        )
        .first()
    )

    if not diagnosis:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Diagnosis record not found "
                "or access denied."
            )
        )

    return diagnosis