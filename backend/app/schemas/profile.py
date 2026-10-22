"""Pydantic schemas for user profiles and interests.

These are used by the V2 profile endpoints.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, validator
from datetime import datetime

class InterestRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ProfileBase(BaseModel):
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, ge=13, le=120)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    profile_picture: Optional[str] = None  # URL or path


class ProfileCreate(ProfileBase):
    interests: Optional[List[str]] = []

    @validator("interests", each_item=True)
    def strip_interest(cls, v: str) -> str:
        return v.strip()

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    profile_picture: Optional[str] = None
    interests: Optional[List[str]] = None

    @validator("interests", each_item=True)
    def strip_interest(cls, v: str) -> str:
        return v.strip()

class ProfileRead(ProfileBase):
    id: int
    user_id: int
    completion_percentage: int
    created_at: datetime
    updated_at: datetime
    interests: List[InterestRead] = []

    class Config:
        from_attributes = True
        orm_mode = True

