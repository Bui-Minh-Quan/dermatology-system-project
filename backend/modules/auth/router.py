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
    # 1. Validate OTP
    if user_in.otp_code != "123456":
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ")

    # 2. Check for duplicate
    existing_user = db.query(User).filter(User.email_phone == user_in.email_phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Người dùng đã tồn tại")

    try:
        # 3. Create User (Now containing Identity data)
        new_user = User(
            email_phone=user_in.email_phone,
            password_hash=security.get_password_hash(user_in.password),
            role=RoleEnum.PATIENT,
            status=UserStatusEnum.ACTIVE,
            full_name=user_in.full_name,
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender
        )
        db.add(new_user)
        db.flush()

        # 4. Create Patient Profile (Now only containing Patient-specific data)
        new_profile = PatientProfile(
            patient_id=new_user.user_id,
            address=user_in.address
        )
        db.add(new_profile)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Đăng ký bệnh nhân thành công"}


# =========================================================
# DOCTOR REGISTRATION
# =========================================================
@router.post("/register/doctor", status_code=status.HTTP_201_CREATED)
def register_doctor(user_in: schemas.DoctorRegister, db: Session = Depends(get_db)):
    # 1. Validate OTP
    if user_in.otp_code != "123456":
        raise HTTPException(status_code=400, detail="Mã OTP không hợp lệ")

    # 2. Check for duplicate account/license
    existing_user = db.query(User).filter(User.email_phone == user_in.email_phone).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Người dùng đã tồn tại")

    existing_license = db.query(DoctorProfile).filter(DoctorProfile.license_number == user_in.license_number).first()
    if existing_license:
        raise HTTPException(status_code=400, detail="Số giấy phép đã được đăng ký")

    try:
        # 3. Create User (Identity data)
        new_user = User(
            email_phone=user_in.email_phone,
            password_hash=security.get_password_hash(user_in.password),
            role=RoleEnum.DOCTOR,
            status=UserStatusEnum.PENDING,
            full_name=user_in.full_name,
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender
        )
        db.add(new_user)
        db.flush()

        # 4. Create Doctor Profile (Professional data only)
        new_profile = DoctorProfile(
            doctor_id=new_user.user_id,
            license_number=user_in.license_number,
            specialty=user_in.specialty,
            workplace=user_in.workplace,
            experience_years=user_in.experience_years,
            bio=user_in.bio,
            degree_image_url=user_in.degree_image_url
        )
        db.add(new_profile)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Đăng ký thành công. Đang chờ Admin duyệt."}


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