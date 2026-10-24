"""V6 -- Report/User model.

Stores user-submitted reports when a user flags another profile or user
for inappropriate behaviour, suspected scam, harassment, etc.
Each report is tied to the reporting user (reporter_id) and the target
(reported_user_id).  Optional profile_id links the report to a specific
profile if applicable.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# Possible report categories
VALID_REPORT_TYPES = [
    "scam",
    "harassment",
    "inappropriate_content",
    "fake_profile",
    "spam",
    "other",
]

# Possible statuses
VALID_REPORT_STATUSES = ["pending", "reviewed", "dismissed"]


class Report(Base):
    """A report filed by one user against another."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id = Column(
        Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )

    report_type = Column(String, nullable=False)  # e.g. "scam", "harassment"
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # JSON string of evidence / metadata

    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    reporter = relationship(
        "User",
        foreign_keys=[reporter_id],
        primaryjoin="Report.reporter_id == User.id",
        backref="reports_filed",
    )
    reported_user = relationship(
        "User",
        foreign_keys=[reported_user_id],
        primaryjoin="Report.reported_user_id == User.id",
        backref="reports_received",
    )
    profile = relationship("Profile")

    __table_args__ = (
        Index("ix_reports_reporter", "reporter_id"),
        Index("ix_reports_reported_user", "reported_user_id"),
        Index("ix_reports_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id} reporter={self.reporter_id} "
            f"reported={self.reported_user_id} type={self.report_type} "
            f"status={self.status}>"
        )
