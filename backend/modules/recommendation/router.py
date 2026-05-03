import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List # ✅ Fixed from 'Typing'
from config.database import get_db
from models.users import User, DoctorProfile, AIDiagnosis
from modules.auth.security import get_current_user
from modules.chatbot_rag.service import GraphRAGService
from . import schemas

router = APIRouter(prefix="/recommendation", tags=["Recommendations"])

@router.post("/doctors", response_model=List[schemas.DoctorRecommendation])
def recommend_doctors(
    request: schemas.RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_specialty = "Dermatology"

    # 1. Extract entities if symptoms are provided
    if request.symptoms:
        entities = GraphRAGService.extract_entities(request.symptoms) # ✅ Fixed typo
        print(f"Extracted entities for recommendation: {entities}")
    
    # 2. Get diagnosis context if available
    if request.diagnosis_id:
        diagnosis = db.query(AIDiagnosis).filter(
            AIDiagnosis.diagnosis_id == request.diagnosis_id, # ✅ Fixed attribute
            AIDiagnosis.patient_id == current_user.user_id    # ✅ Fixed attribute
        ).first()

        if diagnosis:
            print(f"Found diagnosis for recommendation: {diagnosis.predicted_disease}") # ✅ Fixed attribute
        
    # 3. Query doctors
    doctors = db.query(DoctorProfile).filter(
        DoctorProfile.specialty.ilike(f"%{target_specialty}%")
    ).all()

    # 4. Map data and rank
    results = []
    for doctor in doctors:
        # ✅ Fixed: Use request.latitude instead of request.location
        mock_distance = round(random.uniform(1, 20), 1) if request.latitude else None  
        mock_online = random.choice([True, False]) 
        
        results.append(schemas.DoctorRecommendation(
            doctor_id=doctor.doctor_id,
            full_name=doctor.user.full_name, # ✅ Fetched cleanly from the User table!
            specialty=doctor.specialty,
            workplace=doctor.workplace,
            rating_average=doctor.rating_average,
            distance_km=mock_distance,       # ✅ Fixed typo
            avatar_url=doctor.user.avatar_url, # ✅ Fetched cleanly from the User table!
            is_online=mock_online
        ))

    # 5. Sort by rating (Higher is better)
    results.sort(key=lambda x: x.rating_average, reverse=True)

    return results