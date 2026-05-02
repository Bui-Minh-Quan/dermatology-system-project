import os 
import uuid
import shutil
import random
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from config.database import get_db
from models.users import User, AIDiagnosis 
from modules.auth.security import get_current_user 
from . import schemas
from typing import Optional

router = APIRouter(prefix="/diagnosis", tags=["AI Diagnosis"])

# Directory to store uploaded images 
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True) 

@router.post("/", response_model=schemas.DiagnosisResponse)
async def create_diagnosis(
    image: UploadFile = File(...),
    symtoms: Optional[str] = Form(None),
    body_vector: str = Form("0,0,0,0,0,0,0,1"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Save image to disk and get URL
    file_extension = image.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    relative_path = f"static/uploads/{file_name}" # Path for disk
    web_url = f"/static/uploads/{file_name}"      # Path for browser
    
    with open(relative_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # 2. Mock AI results 
    mock_results = [
        {"name": "Acne Vulgaris", "confidence": 0.95, "icd": "L70.0"},
        {"name": "Eczema", "confidence": 0.75, "icd": "L20.9"},
    ]
    result = random.choice(mock_results)

    heatmap_url = f"/static/uploads/heatmap_{file_name}"
    shutil.copy(relative_path, f"static/uploads/heatmap_{file_name}")

    # 3. Save to database
    vector_list = [int(x) for x in body_vector.split(",")]
    new_diagnosis = AIDiagnosis(
        patient_id=current_user.user_id,
        input_image_url=web_url,
        input_symptoms=symtoms,
        input_body_vector=vector_list,
        predicted_disease=result["name"],
        icd10_code=result["icd"], 
        confidence_score=result["confidence"],
        heatmap_url=heatmap_url
    )

    try:
        db.add(new_diagnosis)
        db.commit()
        db.refresh(new_diagnosis)
        
        # Return the object directly
        return new_diagnosis 
        
    except Exception as e:
        db.rollback()
        print(f"🚨 Database Error: {e}") # Help to see error in the logs
        raise HTTPException(status_code=500, detail=str(e))






