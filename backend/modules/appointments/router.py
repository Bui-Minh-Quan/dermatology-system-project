from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date
from datetime import datetime, timedelta
from typing import List
from config.database import get_db
from models.users import User, RoleEnum, Appointment, DoctorProfile, AppointmentStatusEnum
from modules.auth.security import get_current_user
from . import schemas

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/book", response_model=schemas.AppointmentResponse)
def book_appointment(
    appointment_data: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.PATIENT:
        raise HTTPException(status_code=403, detail="Only patients can book appointments")

    # Verify doctor exists
    doctor = db.query(User).filter(
        DoctorProfile.doctor_id == appointment_data.doctor_id,
        User.user_id == DoctorProfile.doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")


    # Collision checking
    # Rule 1: Maximum 2 appoitments per day for each patient
    target_date = appointment_data.appointment_time.date()
    daily_appointments = db.query(Appointment).filter(
        Appointment.patient_id == current_user.user_id,
        cast(Appointment.appointment_time, Date) == target_date,
        Appointment.status.notin_([AppointmentStatusEnum.CANCELLED, AppointmentStatusEnum.REJECTED])
    ).all()

    if len(daily_appointments) >= 2:
        raise HTTPException(status_code=400, detail="You have already booked 2 appointments on this day")

    # Rule 2: Must be 3 hours apart 
    for existing in daily_appointments:
        time_diff = abs((existing.appointment_time - appointment_data.appointment_time).total_seconds()) / 3600
        if time_diff < 3:
            raise HTTPException(status_code=400, detail="Appointments must be at least 3 hours apart")
    
    # Create appointment
    new_appointment = Appointment(
        patient_id=current_user.user_id,
        doctor_id=appointment_data.doctor_id,
        appointment_time=appointment_data.appointment_time,
        status=AppointmentStatusEnum.PENDING
    )

    try:
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        return schemas.AppointmentResponse(
            appointment_id=new_appointment.appointment_id,
            patient_name=current_user.full_name,
            doctor_name=doctor.user.full_name,
            specialty=doctor.specialty,
            workplace=doctor.workplace,
            appointment_time=new_appointment.appointment_time,
            status=new_appointment.status
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to book appointment")


@router.patch("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: str,
    update_data: schemas.AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()

    # Check if appointment exists
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Security check: Only involved patient or doctor can update status
    if current_user.user_id not in [appointment.patient_id, appointment.doctor_id]:
        raise HTTPException(status_code=403, detail="Not authorized to update this appointment")
    
    # --- RULE: 5-Hour Cancellation Policy ---
    if update_data.status == AppointmentStatusEnum.CANCELLED:
        time_until_appt = appointment.appointment_time - datetime.now()
        if time_until_appt < timedelta(hours=5):
            raise HTTPException(
                status_code=400, 
                detail="Bạn chỉ được phép huỷ lịch trước ít nhất 5 tiếng"
            )
    
    # --- RULE: Doctor-Only Actions ---
    doctor_only_states = [
        AppointmentStatusEnum.CONFIRMED, 
        AppointmentStatusEnum.REJECTED, 
        AppointmentStatusEnum.COMPLETED, 
        AppointmentStatusEnum.NO_SHOW
    ]

    if update_data.status in doctor_only_states and current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ mới có thể thực hiện thao tác này")

    # Update status
    appointment.status = update_data.status
    if update_data.reason_for_cancellation:
        appointment.reason_for_cancellation = update_data.reason_for_cancellation
    if update_data.meeting_notes:
        appointment.meeting_notes = update_data.meeting_notes

    try:
        db.commit()
        return {"message": f"Appointment status updated to {update_data.status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update appointment status")

    