import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from config.database import get_db
from models.users import User, DoctorProfile
from modules.auth.security import get_current_user
from . import schemas

router = APIRouter(prefix="/recommendation", tags=["Recommendations"])

@router.post("/doctors", response_model=List[schemas.DoctorRecommendation])
def recommend_doctors(
    request: schemas.RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Query all doctors specializing in Dermatology
    doctors = db.query(DoctorProfile).filter(
        DoctorProfile.specialty.ilike("%Dermatology%")
    ).all()

    results = []
    for doctor in doctors:
        # Mock distance if coordinates are provided
        mock_distance = round(random.uniform(1, 20), 1) if getattr(request, 'latitude', None) else None
        # Mock online status
        mock_online = random.choice([True, False])
        
        results.append(schemas.DoctorRecommendation(
            doctor_id=doctor.doctor_id,
            full_name=doctor.user.full_name,
            specialty=doctor.specialty,
            workplace=doctor.workplace,
            rating_average=doctor.rating_average,
            distance_km=mock_distance,
            avatar_url=doctor.user.avatar_url,
            is_online=mock_online
        ))

    # Sort by rating in descending order, defaulting None to 0
    results.sort(key=lambda x: (x.rating_average or 0), reverse=True)

    return results