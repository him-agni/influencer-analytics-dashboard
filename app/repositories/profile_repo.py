"""
Profile repository — CRUD operations for influencer profiles.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.models.follower_growth import FollowerGrowth
from app.models.engagement_metric import EngagementMetric


class ProfileRepository:
    """Database operations for Profile model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 50) -> list[Profile]:
        result = await self.db.execute(
            select(Profile).offset(skip).limit(limit).order_by(Profile.fetched_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, profile_id: int) -> Optional[Profile]:
        result = await self.db.execute(select(Profile).where(Profile.id == profile_id))
        return result.scalar_one_or_none()

    async def get_by_channel_id(self, channel_id: str) -> Optional[Profile]:
        result = await self.db.execute(
            select(Profile).where(Profile.channel_id == channel_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, data: dict) -> Profile:
        """Insert or update a profile by channel_id."""
        data = {k: v.replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v for k, v in data.items()}
        existing = await self.get_by_channel_id(data["channel_id"])
        if existing:
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            await self.db.flush()
            return existing
        else:
            profile = Profile(**data)
            self.db.add(profile)
            await self.db.flush()
            return profile

    async def get_growth_history(
        self, profile_id: int, limit: int = 365
    ) -> list[FollowerGrowth]:
        result = await self.db.execute(
            select(FollowerGrowth)
            .where(FollowerGrowth.profile_id == profile_id)
            .order_by(FollowerGrowth.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_growth_snapshot(self, data: dict) -> FollowerGrowth:
        data = {k: v.replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v for k, v in data.items()}
        snapshot = FollowerGrowth(**data)
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_engagement_history(
        self, profile_id: int, limit: int = 365
    ) -> list[EngagementMetric]:
        result = await self.db.execute(
            select(EngagementMetric)
            .where(EngagementMetric.profile_id == profile_id)
            .order_by(EngagementMetric.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_engagement_metric(self, data: dict) -> EngagementMetric:
        data = {k: v.replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v for k, v in data.items()}
        metric = EngagementMetric(**data)
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count(Profile.id)))
        return result.scalar_one()
