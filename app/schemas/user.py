from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    display_name: str = Field(..., min_length=2, max_length=128)
    city: str = Field(default="Addis Ababa")
    email: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    language: str = Field(default="en")

class UserLogin(BaseModel):
    username: str
    password: Optional[str] = None

class UserOut(UserBase):
    id: str
    role: str
    public_identifier: str
    is_active: bool
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserPreferenceOut(BaseModel):
    language: str
    notifications_enabled: bool

    class Config:
        from_attributes = True
