"""Pydantic schemas for V4 — Conversation Safety."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class ConversationSafetyRequest(BaseModel):
    """Request body for POST /safety/analyze."""

    message: str = Field(..., min_length=1, max_length=5000,
                         description="Message or conversation snippet to analyze.")


class ConversationSafetyResult(BaseModel):
    """Structured safety result returned to the caller.

    Mirrors the JSON schema documented in the V4 implementation guide.
    """

    risk_level: str = Field(..., description="Overall risk level: low | medium | high")
    categories: List[str] = Field(default_factory=list,
                                  description="List of detected risk categories")
    flagged: bool = Field(..., description="True if any risk category was detected")
    summary: str = Field(..., description="Short human-readable explanation of the result")
    recommendation: str = Field(..., description="Actionable recommendation for the user")

    model_config = ConfigDict(from_attributes=True)


class ConversationSafetyRead(ConversationSafetyResult):
    """Full record as stored / returned from the database."""

    id: int
    user_id: int
    message_snippet: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
