from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import get_db
from models.users import (
    User,
    PatientProfile,
    DoctorProfile,
    RoleEnum,
    UserStatusEnum,
)

from . import schemas, security

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =========================================================
# OTP REQUEST (Mock version)
# =========================================================
@router.post("/request-otp")
def request_otp(otp_request: schemas.OTPRequest, db: Session = Depends(get_db)):
    """
    Request an OTP for registration.
    Currently mocked (always returns 123456).
    """

    # 1. Check if user already exists
    existing_user = db.query(User).filter(
        User.email_phone == otp_request.email_phone
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/Phone already registered"
        )

    # 2. Mock OTP (replace with real email/SMS service later)
    mock_otp = "123456"
    print(f"[MOCK OTP] Sent OTP {mock_otp} to {otp_request.email_phone}")

    return {"message": "OTP sent successfully (use 123456 for testing)"}


# =========================================================
# PATIENT REGISTRATION
# =========================================================
@router.post("/register/patient", status_code=status.HTTP_201_CREATED)
def register_patient(user_in: schemas.PatientRegister, db: Session = Depends(get_db)):
    """
    Register a new patient account + profile.
    """

    # 1. Validate OTP (mock)
    if user_in.otp_code != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # 2. Check for duplicate account
    existing_user = db.query(User).filter(
        User.email_phone == user_in.email_phone
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    try:
        # 3. Create User (authentication layer)
        hashed_pw = security.get_password_hash(user_in.password)

        new_user = User(
            email_phone=user_in.email_phone,
            password_hash=hashed_pw,
            role=RoleEnum.PATIENT,
            status=UserStatusEnum.ACTIVE
        )

        db.add(new_user)
        db.flush()  # Get user_id without committing

        # 4. Create Patient Profile
        new_profile = PatientProfile(
            patient_id=new_user.user_id,
            full_name=user_in.full_name,
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender,
            address=user_in.address
        )

        db.add(new_profile)

        # 5. Commit transaction
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Patient registration completed successfully"}


# =========================================================
# DOCTOR REGISTRATION
# =========================================================
@router.post("/register/doctor", status_code=status.HTTP_201_CREATED)
def register_doctor(user_in: schemas.DoctorRegister, db: Session = Depends(get_db)):
    """
    Register a doctor account.
    Doctors require admin approval before becoming ACTIVE.
    """

    # 1. Validate OTP (mock)
    if user_in.otp_code != "123456":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # 2. Check for duplicate account
    existing_user = db.query(User).filter(
        User.email_phone == user_in.email_phone
    ).first()

    # 3. Check if License Number is already registered
    existing_license = db.query(DoctorProfile).filter(
        DoctorProfile.license_number == user_in.license_number
    ).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License number already registered"
        )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

    try:
        # 3. Create User (pending status)
        hashed_pw = security.get_password_hash(user_in.password)

        new_user = User(
            email_phone=user_in.email_phone,
            password_hash=hashed_pw,
            role=RoleEnum.DOCTOR,
            status=UserStatusEnum.PENDING
        )

        db.add(new_user)
        db.flush()

        # 4. Create Doctor Profile
        new_profile = DoctorProfile(
            doctor_id=new_user.user_id,
            license_number=user_in.license_number,
            specialty=user_in.specialty,
            workplace=user_in.workplace,
            degree_image_url=user_in.degree_image_url,
        )

        db.add(new_profile)

        # 5. Commit transaction
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Registration completed. Waiting for admin approval."}


# =========================================================
# LOGIN
# =========================================================
@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token along with user profile details.
    """

    # 1. Find user
    user = db.query(User).filter(
        User.email_phone == user_in.email_phone
    ).first()

    # 2. Verify credentials
    if not user or not security.verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/phone or password"
        )

    # 3. Check account status
    if user.status != UserStatusEnum.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

    # 4. Create JWT token
    access_token = security.create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )

    # 5. Return token + role + status directly to the frontend
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "status": user.status
    }