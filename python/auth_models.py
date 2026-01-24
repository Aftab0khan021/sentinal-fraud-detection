"""
Authentication request/response models for SentinAL API.
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
