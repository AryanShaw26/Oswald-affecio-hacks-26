"""Pydantic schemas for V6 -- Blocks."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class BlockBase(BaseModel):
    """Base fields shared by all block schemas."""

    blocked_user_id: int = Field(..., description="ID of the user to block.")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for the block.")


class BlockCreate(BlockBase):
    """Request body for POST /blocks."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "blocked_user_id": 42,
                "reason": "This user is behaving inappropriately.",
            }
        }
    )


class BlockRead(BaseModel):
    """Full block record returned from the database."""

    id: int
    blocker_id: int
    blocked_id: int
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockResponse(BaseModel):
    """Convenience wrapper returned after creating a block."""

    id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
