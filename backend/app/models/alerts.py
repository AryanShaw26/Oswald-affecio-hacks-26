"""V6 -- Safety Alert model.

Stores safety-related alerts that are generated when a user reports
another user, blocks someone, or when a system-level safety event
occurs (e.g. a high-risk conversation safety scan).  Each alert is
owned by the user who should see it and supports a soft-read flag.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# Possible alert types
VALID_ALERT_TYPES = [
    "report_created",
    "block_applied",
    "high_risk_conversation",
    "privacy_breach",
    "system_notification",
]

# Possible severity levels
VALID_ALERT_SEVERITIES = ["low", "medium", "high"]


class Alert(Base):
    """A safety alert notification for a user."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    # Optional links to related objects
    related_report_id = Column(
        Integer, ForeignKey("reports.id", ondelete="SET NULL"), nullable=True
    )
    related_block_id = Column(
        Integer, ForeignKey("blocks.id", ondelete="SET NULL"), nullable=True
    )

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", lazy="joined")
    related_report = relationship("Report", lazy="joined")
    related_block = relationship("Block", lazy="joined")

    __table_args__ = (
        Index("ix_alerts_user", "user_id"),
        Index("ix_alerts_read", "is_read"),
        Index("ix_alerts_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} user_id={self.user_id} "
            f"type={self.alert_type} severity={self.severity} "
            f"read={self.is_read}>"
        )
