"""V4 — Conversation Safety models.

Stores structured safety analysis results produced by the AI Safety Analyzer.
Each record is associated with the authenticated user who submitted the
message, and only ever returned to that user (user isolation).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ConversationSafety(Base):
    """Persisted conversation-safety analysis for a single user submission."""

    __tablename__ = "conversation_safety_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Store only a truncated excerpt for the user's own reference (V4 requirement:
    # avoid storing unnecessary sensitive message content).
    message_snippet = Column(Text, nullable=True)  # truncated to ~500 chars

    # Structured result fields
    risk_level = Column(String, nullable=False)  # 'low' | 'medium' | 'high'
    categories = Column(Text, nullable=False)  # JSON array, e.g. ["financial_request", "scam"]
    flagged = Column(Boolean, default=False, nullable=False)
    summary = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_conversation_safety_user", "user_id"),
        Index("ix_conversation_safety_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ConversationSafety user_id={self.user_id} risk={self.risk_level} flagged={self.flagged}>"
