import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password exceeds bcrypt maximum length of 72 bytes")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password against strength requirements.

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    errors = []

    if len(password) < settings.min_password_length:
        errors.append(
            f"Password must be at least {settings.min_password_length} characters long"
        )

    if len(password.encode("utf-8")) > 72:
        errors.append("Password must be 72 bytes or fewer for bcrypt compatibility")

    if settings.require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.require_digit and not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")

    if settings.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append(
            "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
        )

    if errors:
        return False, "; ".join(errors)

    return True, None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to include in the token
        expires_delta: Custom expiration time (default: JWT_EXPIRATION_HOURS from config)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token claims, or None if token is invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise
