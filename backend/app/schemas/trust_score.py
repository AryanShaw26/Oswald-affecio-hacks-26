"""Trust Engine Pydantic schemas for V3."""

from datetime import datetime
from typing import List, Dict, Any

from pydantic import BaseModel, ConfigDict


class TrustFactorBreakdown(BaseModel):
    """A single factor that contributes to the overall trust score."""

    name: str
    weight: float  # 0-1
    score: int  # 0-100
    contribution: int  # score * weight (rounded)
    details: str = ""

    model_config = ConfigDict(from_attributes=True)


class TrustScoreRead(BaseModel):
    """Full trust-score response returned by the API."""

    id: int
    user_id: int | None = None
    profile_id: int | None = None
    score: int
    risk_level: str
    explanation: str
    factor_data: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TrustScoreResponse(BaseModel):
    """Convenience wrapper that returns parsed factor data alongside the score."""

    score: int
    risk_level: str
    explanation: str
    factors: List[TrustFactorBreakdown]

    model_config = ConfigDict(from_attributes=True)