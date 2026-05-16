"""
Hashtag model — tracks tags extracted from video titles/descriptions.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Hashtag(Base):
    """Hashtag extracted from a YouTube video title or description."""

    __tablename__ = "hashtags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    frequency: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    post = relationship("Post", back_populates="hashtags")

    def __repr__(self) -> str:
        return f"<Hashtag(tag=#{self.tag}, frequency={self.frequency})>"
