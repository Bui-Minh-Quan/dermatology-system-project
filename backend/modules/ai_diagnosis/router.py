import os
import uuid
import shutil
import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from config.database import get_db
from models.users import User, AIDiagnosis
from modules.auth.security import get_current_user
from . import schemas

load_dotenv()

router = APIRouter(prefix="/diagnosis", tags=["AI Diagnosis"])

# Load config from .env
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
HEATMAP_DIR = os.getenv("HEATMAP_DIR", "static/heatmaps")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))  # default 5MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(HEATMAP_DIR, exist_ok=True)

# Allowed image types
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/", response_model=schemas.DiagnosisResponse)
async def create_diagnosis(
    image: UploadFile = File(...),
    symptoms: Optional[str] = Form(None),
    body_vector: str = Form("0,0,0,0,0,0,0,1"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # -------------------------------
    # 1. Validate file type
    # -------------------------------
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, PNG, WEBP allowed."
        )

    file_extension = image.filename.split(".")[-1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension."
        )

    # -------------------------------
    # 2. Validate file size
    # -------------------------------
    contents = await image.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Max size is 5MB."
        )

    # Reset file pointer after reading
    image.file.seek(0)

    # -------------------------------
    # 3. Save file
    # -------------------------------
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    web_url = f"/static/uploads/{file_name}"

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # -------------------------------
        # 4. Mock AI processing
        # -------------------------------
        mock_results = [
            {"name": "Acne Vulgaris", "confidence": 0.95, "icd": "L70.0"},
            {"name": "Eczema", "confidence": 0.75, "icd": "L20.9"},
        ]
        result = random.choice(mock_results)

        # Fake heatmap
        heatmap_filename = f"heatmap_{file_name}"
        heatmap_path = os.path.join(HEATMAP_DIR, heatmap_filename)
        shutil.copy(file_path, heatmap_path)

        heatmap_url = f"/static/heatmaps/{heatmap_filename}"

        # -------------------------------
        # 5. Process body vector
        # -------------------------------
        try:
            vector_list = [int(x) for x in body_vector.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid body_vector format")

        # -------------------------------
        # 6. Save to database
        # -------------------------------
        new_diagnosis = AIDiagnosis(
            patient_id=current_user.user_id,
            input_image_url=web_url,
            input_symptoms=symptoms,
            input_body_vector=vector_list,
            predicted_disease=result["name"],
            icd10_code=result["icd"],
            confidence_score=result["confidence"],
            heatmap_url=heatmap_url
        )

        db.add(new_diagnosis)
        db.commit()
        db.refresh(new_diagnosis)

        return new_diagnosis

    except Exception as e:
        # -------------------------------
        # 7. Cleanup on failure
        # -------------------------------
        db.rollback()

        if os.path.exists(file_path):
            os.remove(file_path)

        if 'heatmap_path' in locals() and os.path.exists(heatmap_path):
            os.remove(heatmap_path)

        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")