from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    full_name: str


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    full_name: str

    class Config:
        from_attributes = True
