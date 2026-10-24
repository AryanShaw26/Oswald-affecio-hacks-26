"""Pydantic schemas for V6 -- Reports."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ReportBase(BaseModel):
    """Base fields shared by all report schemas."""

    report_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Category of the report (e.g. scam, harassment, spam, fake_profile, inappropriate_content, other).",
    )
    description: str = Field(..., min_length=1, max_length=2000, description="Detailed description of the issue.")


class ReportCreate(ReportBase):
    """Request body for POST /reports."""

    reported_user_id: int = Field(..., description="ID of the user being reported.")
    profile_id: Optional[int] = Field(None, description="Optional profile ID the report relates to.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reported_user_id": 42,
                "report_type": "scam",
                "description": "This user is requesting money and asking for my bank details.",
                "profile_id": 15,
            }
        }
    )


class ReportRead(ReportBase):
    """Full report record returned from the database."""

    id: int
    reporter_id: int
    reported_user_id: int
    profile_id: Optional[int] = None
    status: str
    evidence: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    """Convenience wrapper returned after creating a report."""

    id: int
    report_type: str
    status: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
