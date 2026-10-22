"""Security utilities for password hashing and JWT handling.

Uses ``passlib`` for password hashing (bcrypt) and ``python-jose`` for JWT
creation/verification. The secret key is taken from the Settings (``SECRET_KEY``).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for *password*.

    The function is a thin wrapper around ``passlib`` and raises no exceptions.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*.
    """
    return pwd_context.verify(plain_password, hashed_password)

# ---------------------------------------------------------------------------
# JWT handling
# ---------------------------------------------------------------------------
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token.

    ``data`` should contain at least a ``sub`` claim identifying the user (e.g.
    the user id). An optional ``expires_delta`` can be supplied; otherwise the
    token lives for ``ACCESS_TOKEN_EXPIRE_MINUTES``.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode a JWT token and return the payload.

    Raises ``JWTError`` if validation fails.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    return payload

