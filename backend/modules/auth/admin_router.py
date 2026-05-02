from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.database import get_db
from models.users import User, UserStatusEnum, RoleEnum, DoctorProfile
from .security import require_admin
from uuid import UUID

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

@router.get("/pending-accounts")
def get_pending_accounts(db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    pending_users = db.query(User).filter(User.status == UserStatusEnum.PENDING).all()
    return {"pending_accounts": pending_users}

@router.post("/approve/{user_id}")
def approve_account(user_id: UUID, db: Session = Depends(get_db), admin_user: User = Depends(require_admin)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status != UserStatusEnum.PENDING:
        raise HTTPException(status_code=400, detail="User is not pending approval")

    user.status = UserStatusEnum.ACTIVE
    db.add(user)
    db.commit()
    return {"message": f"User {user.email_phone} approved successfully"}

