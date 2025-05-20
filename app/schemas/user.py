from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserSocialCreate(UserBase):
    oauth_provider: str
    oauth_id: str
    profile_image: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class SubscriptionUpdate(BaseModel):
    subscription_tier: str
    subscription_end: datetime

class UserResponse(UserBase):
    id: int
    oauth_provider: Optional[str] = None
    profile_image: Optional[str] = None
    subscription_tier: str
    subscription_end: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 