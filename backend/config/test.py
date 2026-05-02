from config.database import postgres_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from models.users import User, PatientProfile, DoctorProfile

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
db = SessionLocal()

db.query(DoctorProfile).delete()
db.query(PatientProfile).delete()
db.query(User).delete()
db.commit()