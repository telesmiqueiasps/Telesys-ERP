from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.core.config import settings

# Initialize Argon2id password hasher
password_hash = PasswordHash((Argon2Hasher(),))


def get_password_hash(password: str) -> str:
    """Generates an Argon2id hash for the given plain password."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str | Any, claims: Optional[Dict[str, Any]] = None, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a JWT access token for a user subject."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    if claims:
        to_encode.update(claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a JWT refresh token for a user subject."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Token inválido ou expirado: {str(e)}")
