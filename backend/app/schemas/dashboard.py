"""Pydantic schemas for V6 -- Dashboard aggregation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DashboardTrustScore(BaseModel):
    """Trust score summary for the dashboard."""

    score: int
    risk_level: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardAlert(BaseModel):
    """Compact alert representation for the dashboard."""

    id: int
    alert_type: str
    severity: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardReport(BaseModel):
    """Compact report representation for the dashboard."""

    id: int
    report_type: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Aggregated dashboard data for the authenticated user."""

    user_id: int
    user_name: str
    user_email: str
    trust_score: Optional[DashboardTrustScore] = None
    recent_alerts: list[DashboardAlert] = []
    recent_reports: list[DashboardReport] = []
    blocks_given_count: int = 0
    blocks_received_count: int = 0
    reports_count: int = 0
    alerts_count: int = 0
    unread_alerts_count: int = 0

    model_config = ConfigDict(from_attributes=True)
