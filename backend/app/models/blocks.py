"""V6 -- Block/User model.

Stores block relationships: user A blocks user B so that B's content
and interactions are hidden from A.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Block(Base):
    """A block relationship between two users."""

    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blocked_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason = Column(Text, nullable=True)  # optional free-text reason
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    blocker = relationship(
        "User",
        foreign_keys=[blocker_id],
        primaryjoin="Block.blocker_id == User.id",
        backref="blocks_given",
    )
    blocked = relationship(
        "User",
        foreign_keys=[blocked_id],
        primaryjoin="Block.blocked_id == User.id",
        backref="blocks_received",
    )

    __table_args__ = (
        # A user can only block another user once
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_blocker_blocked"),
        Index("ix_blocks_blocker", "blocker_id"),
        Index("ix_blocks_blocked", "blocked_id"),
    )

    def __repr__(self) -> str:
        return f"<Block blocker={self.blocker_id} blocked={self.blocked_id}>"
