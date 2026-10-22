"""FastAPI dependencies for authentication.

Provides a ``get_current_user`` dependency that extracts and validates a JWT
from the ``Authorization: Bearer <token>`` header and returns the ``User``
SQLAlchemy model instance.
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jose import JWTError

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.utils.security import decode_access_token

bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT and return the corresponding ``User``.

    Raises ``401 Unauthorized`` if the token is missing, invalid, or the user
    does not exist.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

