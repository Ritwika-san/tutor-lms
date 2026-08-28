from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import RoleEnum


class UserBase(BaseModel):
    """Base user schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr


class UserRegisterRequest(UserBase):
    """Request schema for user registration."""

    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters with uppercase, digit, and special character",
    )
    role: RoleEnum = Field(default=RoleEnum.STUDENT, description="User role")


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Response schema for user data (excludes sensitive fields)."""

    id: int
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response schema for authentication token."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str
    status_code: int = Field(..., ge=400, le=599)


class ValidationErrorDetail(BaseModel):
    """Detail of a validation error."""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors."""

    detail: list[ValidationErrorDetail]
    status_code: int = 422
