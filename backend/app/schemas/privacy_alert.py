"""Pydantic schemas for V5 — Privacy Guardian."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class PrivacyCheckRequest(BaseModel):
    """Request body for POST /privacy/check."""

    message: str = Field(..., min_length=1, max_length=5000,
                         description="Message text to scan for sensitive information.")


class PrivacyResult(BaseModel):
    """Structured privacy result returned to the caller.

    Mirrors the JSON schema documented in the V5 implementation guide.
    """

    flagged: bool = Field(..., description="True if any sensitive information was detected")
    risk_level: str = Field(..., description="Overall risk level: low | medium | high")
    detected_types: List[str] = Field(default_factory=list,
                                       description="Types of sensitive information detected")
    warning: str = Field(..., description="Human-readable warning message")
    recommendation: str = Field(...,
                                description="Actionable recommendation (remove, redact, avoid sharing)")

    model_config = ConfigDict(from_attributes=True)


class PrivacyAlertRead(BaseModel):
    """Full alert record as stored / returned from the database."""

    id: int
    user_id: int
    detected_types: List[str]
    flagged: bool
    risk_level: str
    warning: str
    recommendation: str
    message_excerpt: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
