"""
Engagement metrics model — aggregated engagement stats per profile per day.
"""

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EngagementMetric(Base):
    """Daily aggregated engagement metrics for a profile."""

    __tablename__ = "engagement_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_likes: Mapped[float] = mapped_column(Float, default=0.0)
    avg_comments: Mapped[float] = mapped_column(Float, default=0.0)
    avg_views: Mapped[float] = mapped_column(Float, default=0.0)
    total_posts: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    profile = relationship("Profile", back_populates="engagement_metrics")

    def __repr__(self) -> str:
        return f"<EngagementMetric(profile_id={self.profile_id}, date={self.date}, rate={self.engagement_rate:.2f}%)>"
