import os
from config.database import SessionLocal
from models.users import User, RoleEnum, UserStatusEnum
from modules.auth.security import get_password_hash


def seed_admin():
    db = SessionLocal()

    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@dermatology.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "SuperSecretAdmin123")

        # Check if admin already exists
        admin_exists = db.query(User).filter(
            User.email_phone == admin_email
        ).first()

        if not admin_exists:
            admin_user = User(
                email_phone=admin_email,
                password_hash=get_password_hash(admin_password),
                role=RoleEnum.ADMIN,
                status=UserStatusEnum.ACTIVE
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