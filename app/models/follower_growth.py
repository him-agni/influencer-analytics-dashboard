"""
Follower / Subscriber growth snapshot model.
One row per profile per day to track growth over time.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FollowerGrowth(Base):
    """Daily snapshot of a channel's subscriber and view counts."""

    __tablename__ = "follower_growth"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    subscribers: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    video_count: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="follower_snapshots")

    def __repr__(self) -> str:
        return f"<FollowerGrowth(profile_id={self.profile_id}, subs={self.subscribers}, date={self.timestamp})>"
