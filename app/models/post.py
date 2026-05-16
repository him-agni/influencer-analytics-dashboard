"""
Post / Video model.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Post(Base):
    """Represents a YouTube video (or future Instagram post)."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[Optional[str]] = mapped_column(String(50))  # video, short, live
    duration: Mapped[Optional[str]] = mapped_column(String(50))  # ISO 8601 duration
    likes: Mapped[int] = mapped_column(BigInteger, default=0)
    comments_count: Mapped[int] = mapped_column(BigInteger, default=0)
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    favorites: Mapped[int] = mapped_column(BigInteger, default=0)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    hashtags = relationship("Hashtag", back_populates="post", cascade="all, delete-orphan")

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate: (likes + comments) / views × 100."""
        if self.views == 0:
            return 0.0
        return ((self.likes + self.comments_count) / self.views) * 100

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, video_id={self.video_id}, title={self.title[:40]})>"
