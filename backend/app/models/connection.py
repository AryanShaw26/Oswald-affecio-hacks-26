from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    requester = relationship("User", foreign_keys=[requester_id], backref="outgoing_connections")
    target_user = relationship("User", foreign_keys=[target_user_id], backref="incoming_connections")

    __table_args__ = (
        UniqueConstraint("requester_id", "target_user_id", name="uq_connection_request"),
        Index("ix_connections_requester_target", "requester_id", "target_user_id"),
    )

    def __repr__(self) -> str:
        return f"<Connection {self.requester_id}->{self.target_user_id} ({self.status})>"
