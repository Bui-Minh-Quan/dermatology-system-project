from datetime import datetime
from config.database import SessionLocal, postgres_engine
from models.users import Base, User, RoleEnum, UserStatusEnum
from modules.auth.security import get_password_hash

def seed_admin():
    print("🛠️ Synchronizing database tables...")
    Base.metadata.create_all(bind=postgres_engine)
    
    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.email_phone == "admin@dermatology.com").first()
        
        if not admin_exists:
            admin_user = User(
                email_phone="admin@dermatology.com",
                password_hash=get_password_hash("SuperSecretAdmin123"), 
                role=RoleEnum.ADMIN,
                status=UserStatusEnum.ACTIVE,
                full_name="System Administrator",
                date_of_birth=datetime(1990, 1, 1),
                gender="Other"
            )
            db.add(admin_user)
            db.commit()
            print("✅ Super Admin created successfully.")
        else:
            print("ℹ️ Admin already exists.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()