"""V5 — Privacy Guardian models.

Stores privacy alerts generated when sensitive information is detected in a
user's message text.  Only the *type* of sensitive data and a minimal
excerpt are persisted — never the full sensitive value (V5 requirement).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class PrivacyAlert(Base):
    """Persisted privacy alert for the authenticated user."""

    __tablename__ = "privacy_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # JSON array of detected types, e.g. ["phone_number", "upi_id"]
    detected_types = Column(Text, nullable=False)
    flagged = Column(Boolean, default=False, nullable=False)
    risk_level = Column(String, nullable=False, default="high")  # 'low' | 'medium' | 'high'
    warning = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    # Minimal excerpt only — never store the raw sensitive value.
    message_excerpt = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_privacy_alerts_user", "user_id"),
        Index("ix_privacy_alerts_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PrivacyAlert user_id={self.user_id} types={self.detected_types} flagged={self.flagged}>"