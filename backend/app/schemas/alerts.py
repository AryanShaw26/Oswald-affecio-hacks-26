"""Pydantic schemas for V6 -- Alerts (Safety Alerts)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AlertRead(BaseModel):
    """Full alert record as stored / returned from the database."""

    id: int
    user_id: int
    alert_type: str
    severity: str
    message: str
    is_read: bool
    related_report_id: Optional[int] = None
    related_block_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertResponse(BaseModel):
    """Convenience wrapper for alert listing / summary responses."""

    alerts: list[AlertRead]
    unread_count: int
    total_count: int

    model_config = ConfigDict(from_attributes=True)
