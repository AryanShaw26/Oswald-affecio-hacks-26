"""Trust Engine models for V3.

Defines ``TrustScore`` (current/latest assessment) and the optional
``TrustScoreHistory`` table that keeps a chronological record of every
re-calculation.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrustScore(Base):
    """Current/latest trust assessment for a user/profile pair."""

    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(String, nullable=False)  # 'low' | 'moderate' | 'higher'
    explanation = Column(Text, nullable=False)
    factor_data = Column(Text, nullable=False)  # JSON string of factor breakdown
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    profile = relationship("Profile")

    __table_args__ = (
        Index("ix_trust_scores_user", "user_id"),
        Index("ix_trust_scores_profile", "profile_id"),
    )

    def __repr__(self) -> str:
        return f"<TrustScore user_id={self.user_id} score={self.score} risk={self.risk_level}>"


class TrustScoreHistory(Base):
    """Historical record of trust score assessments (optional, append-only)."""

    __tablename__ = "trust_score_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    factor_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_trust_score_history_user", "user_id"),
        Index("ix_trust_score_history_profile", "profile_id"),
        Index("ix_trust_score_history_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TrustScoreHistory user_id={self.user_id} score={self.score}>"