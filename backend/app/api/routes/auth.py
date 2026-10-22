"""Authentication routes for V2.

- POST /auth/register – create a new user with hashed password.
- POST /auth/login – verify credentials and return JWT token.
- GET /users/me – return current user info (protected).
- POST /auth/logout – client‑side operation; just a placeholder 200 response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.user import UserRead
from app.utils.security import hash_password, verify_password, create_access_token
from app.core.database import get_db
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check duplicate email
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)

@router.post("/logout")
def logout():
    # Stateless JWT – client simply removes token. Return 200 for convenience.
    return {"message": "Logged out"}

# Public endpoint to fetch current user info (protected)
@router.get("/users/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user

