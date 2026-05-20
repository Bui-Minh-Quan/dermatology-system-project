import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, ARRAY, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from config.database import Base


# ENUMS
class RoleEnum(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class UserStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    LOCKED = "locked"


class DiagnosisStatusEnum(str, enum.Enum):
    PENDING = "pending"           # Uploaded, waiting in Redis queue
    PROCESSING = "processing"     # Worker picked it up
    COMPLETED = "completed"       # Trimodal model finished, heatmap generated
    REJECTED = "rejected"         # MobileNet gatekeeper said "Not Skin"
    FAILED = "failed"             # System error


class AppointmentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class TrackingStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


# 1. USERS & PROFILES
class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_phone = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    status = Column(SQLEnum(UserStatusEnum), default=UserStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    full_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)


class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    address = Column(String, nullable=True) 

    user = relationship("User", back_populates="patient_profile")
    diagnoses = relationship("AIDiagnosis", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    tracking_sessions = relationship("TrackingSession", back_populates="patient")
    medical_info = relationship("PatientMedicalInfo", back_populates="patient")

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    license_number = Column(String, unique=True, nullable=False)
    specialty = Column(String, nullable=False)
    workplace = Column(String, nullable=False)
    experience_years = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    degree_image_url = Column(String, nullable=False)
    rating_average = Column(Float, default=0.0)

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")

    
class PatientMedicalInfo(Base):
    __tablename__ = "patient_medical_info"
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.patient_id"), primary_key=True)
    blood_type = Column(String, nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    medical_notes = Column(Text, nullable=True)
    is_smoker = Column(String, nullable=True)
    is_alcoholic = Column(String, nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    is_pregnant = Column(String, nullable=True)

    patient = relationship("PatientProfile", back_populates="medical_info")

# 2. AI DIAGNOSIS
class AIDiagnosis(Base):
    __tablename__ = "ai_diagnosis"
    diagnosis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.patient_id"), nullable=False)

    # Status Tracking for Background Worker
    status = Column(SQLEnum(DiagnosisStatusEnum, values_callable=lambda obj: [e.value for e in obj]), default=DiagnosisStatusEnum.PENDING)
    error_message = Column(Text, nullable=True) # E.g., "Image rejected by gatekeeper"

    input_image_url = Column(String, nullable=False)
    input_symptoms = Column(Text, nullable=True)
    input_body_vector = Column(ARRAY(SmallInteger), nullable=True) # 8-dimensions

    predicted_disease = Column(String, nullable=True)
    icd10_code = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    heatmap_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("PatientProfile", back_populates="diagnoses")


# 3. Tracking progress
class TrackingSession(Base):
    __tablename__ = "tracking_sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.patient_id"), nullable=False)
    
    session_name = Column(String, nullable=False)
    target_disease = Column(String, nullable=True)
    status = Column(SQLEnum(TrackingStatusEnum), default=TrackingStatusEnum.ACTIVE)

    patient = relationship("PatientProfile", back_populates="tracking_sessions")
    logs = relationship("TrackingLog", back_populates="session")


class TrackingLog(Base):
    __tablename__ = "tracking_logs"
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("tracking_sessions.session_id"), nullable=False)

    image_url = Column(String, nullable=False)
    delta_area = Column(Float, nullable=True)
    delta_color = Column(Float, nullable=True)
    delta_texture = Column(Float, nullable=True)
    doctor_notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TrackingSession", back_populates="logs")


# 4. Appointment and Sharing
class Appointment(Base):
    __tablename__ = "appointments"
    appointment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.patient_id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctor_profiles.doctor_id"), nullable=False)

    appointment_time = Column(DateTime, nullable=False)
    status = Column(SQLEnum(AppointmentStatusEnum), default=AppointmentStatusEnum.PENDING)
    reason_for_cancellation = Column(Text, nullable=True)
    meeting_notes = Column(Text, nullable=True)

    patient = relationship("PatientProfile", back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")


class MedicalRecordSharing(Base):
    __tablename__ = "medical_records_sharing"
    sharing_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient_profiles.patient_id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctor_profiles.doctor_id"), nullable=False)

    access_granted_at = Column(DateTime, default=datetime.utcnow)
    access_expired_at = Column(DateTime, nullable=True)

