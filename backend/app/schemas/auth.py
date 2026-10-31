from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role: Optional[str] = "analyst"
    organization: Optional[str] = "Urban Analytics Division"
    preferred_city: Optional[str] = "Chennai"

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or len(cleaned) < 3:
            raise ValueError("Please enter a valid email address containing '@'.")
        return cleaned


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    organization: Optional[str] = None
    preferred_city: Optional[str] = None
    role: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    current_password: Optional[str] = None
    new_password: str = Field(..., min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    organization: Optional[str] = None
    preferred_city: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
