"""Profile related models: User profile, interests, many‑to‑many link."""

from datetime import datetime, timezone
from sqlalchemy import Table, Column, Integer, String, ForeignKey, UniqueConstraint, Index, DateTime
from sqlalchemy.orm import relationship



from app.core.database import Base

# Association table for many‑to‑many profile ↔ interest
profile_interests = Table(
    "profile_interests",
    Base.metadata,
    Column("profile_id", Integer, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("profile_id", "interest_id", name="uq_profile_interest"),
    Index("ix_profile_interest_profile", "profile_id"),
    Index("ix_profile_interest_interest", "interest_id"),
)

class Interest(Base):
    __tablename__ = "interests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Interest {self.name}>"

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)  # store URL or path
    completion_percentage = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # relationships
    user = relationship("User", back_populates="profile")
    interests = relationship("Interest", secondary=profile_interests, backref="profiles")

    def __repr__(self) -> str:
        return f"<Profile {self.id} for user {self.user_id}>"

