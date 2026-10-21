from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/test-user", response_model=UserRead)
def create_test_user(payload: UserCreate, db: Session = Depends(get_db)):
    """V1 dev-only: insert a test user to verify DB write."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/test-user/{user_id}", response_model=UserRead)
def get_test_user(user_id: int, db: Session = Depends(get_db)):
    """V1 dev-only: retrieve a test user to verify DB read."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

