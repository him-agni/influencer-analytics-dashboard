"""
Influencer / Channel profile model.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Profile(Base):
    """Represents a YouTube channel (or future Instagram profile)."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, default="youtube")
    channel_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(512))
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(512))
    subscribers: Mapped[int] = mapped_column(BigInteger, default=0)
    total_views: Mapped[int] = mapped_column(BigInteger, default=0)
    video_count: Mapped[int] = mapped_column(BigInteger, default=0)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    country: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # channel creation date
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    posts = relationship("Post", back_populates="profile", cascade="all, delete-orphan")
    follower_snapshots = relationship(
        "FollowerGrowth", back_populates="profile", cascade="all, delete-orphan"
    )
    engagement_metrics = relationship(
        "EngagementMetric", back_populates="profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, platform={self.platform}, username={self.username})>"
