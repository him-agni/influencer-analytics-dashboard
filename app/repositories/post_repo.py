"""
Post repository — CRUD operations for videos/posts.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post
from app.models.comment import Comment
from app.models.hashtag import Hashtag


class PostRepository:
    """Database operations for Post, Comment, and Hashtag models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Posts ──────────────────────────────────────────────────

    async def get_by_profile(
        self, profile_id: int, skip: int = 0, limit: int = 50, sort_by: str = "published_at"
    ) -> list[Post]:
        order_col = getattr(Post, sort_by, Post.published_at)
        result = await self.db.execute(
            select(Post).where(Post.profile_id == profile_id)
            .order_by(order_col.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_video_id(self, video_id: str) -> Optional[Post]:
        result = await self.db.execute(select(Post).where(Post.video_id == video_id))
        return result.scalar_one_or_none()

    async def upsert(self, data: dict) -> Post:
        data = {k: v.replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v for k, v in data.items()}
        existing = await self.get_by_video_id(data["video_id"])
        if existing:
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            await self.db.flush()
            return existing
        else:
            post = Post(**data)
            self.db.add(post)
            await self.db.flush()
            return post

    async def get_top_posts(self, profile_id: int, limit: int = 5, metric: str = "views") -> list[Post]:
        order_col = getattr(Post, metric, Post.views)
        result = await self.db.execute(
            select(Post).where(Post.profile_id == profile_id)
            .order_by(order_col.desc()).limit(limit)
        )
        return list(result.scalars().all())

    # ── Comments ──────────────────────────────────────────────

    async def get_comments(self, post_id: int, limit: int = 100) -> list[Comment]:
        result = await self.db.execute(
            select(Comment).where(Comment.post_id == post_id)
            .order_by(Comment.likes.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_comments_by_profile(self, profile_id: int, limit: int = 500) -> list[Comment]:
        result = await self.db.execute(
            select(Comment).join(Post).where(Post.profile_id == profile_id)
            .order_by(Comment.likes.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def upsert_comment(self, data: dict) -> Comment:
        data = {k: v.replace(tzinfo=None) if isinstance(v, datetime) and v.tzinfo else v for k, v in data.items()}
        result = await self.db.execute(
            select(Comment).where(Comment.comment_id == data["comment_id"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            for key, value in data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            await self.db.flush()
            return existing
        else:
            comment = Comment(**data)
            self.db.add(comment)
            await self.db.flush()
            return comment

    # ── Hashtags ──────────────────────────────────────────────

    async def upsert_hashtag(self, post_id: int, tag: str, frequency: int = 1) -> Hashtag:
        result = await self.db.execute(
            select(Hashtag).where(Hashtag.post_id == post_id, Hashtag.tag == tag)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.frequency = frequency
            await self.db.flush()
            return existing
        else:
            hashtag = Hashtag(post_id=post_id, tag=tag, frequency=frequency)
            self.db.add(hashtag)
            await self.db.flush()
            return hashtag

    async def get_top_hashtags(self, profile_id: int, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(Hashtag.tag, func.sum(Hashtag.frequency).label("total"))
            .join(Post).where(Post.profile_id == profile_id)
            .group_by(Hashtag.tag).order_by(func.sum(Hashtag.frequency).desc())
            .limit(limit)
        )
        return [{"tag": row.tag, "frequency": row.total} for row in result.all()]

    async def count_posts(self) -> int:
        result = await self.db.execute(select(func.count(Post.id)))
        return result.scalar_one()

    async def count_comments(self) -> int:
        result = await self.db.execute(select(func.count(Comment.id)))
        return result.scalar_one()

    async def get_average_engagement_rate(self) -> float:
        result = await self.db.execute(
            select(
                func.sum(Post.likes + Post.comments_count),
                func.sum(Post.views)
            )
        )
        totals = result.first()
        if not totals or not totals[1] or totals[1] == 0:
            return 0.0
        return round((totals[0] / totals[1]) * 100, 4)

    async def get_hashtag_sov(self, profile_ids: list[int], limit: int = 10) -> list[dict]:
        top_tags_stmt = (
            select(Hashtag.tag)
            .join(Post)
            .where(Post.profile_id.in_(profile_ids))
            .group_by(Hashtag.tag)
            .order_by(func.sum(Hashtag.frequency).desc())
            .limit(limit)
        )
        top_tags = (await self.db.execute(top_tags_stmt)).scalars().all()

        if not top_tags:
            return []

        sov_stmt = (
            select(Hashtag.tag, Post.profile_id, func.sum(Hashtag.frequency).label("freq"))
            .join(Post)
            .where(Post.profile_id.in_(profile_ids))
            .where(Hashtag.tag.in_(top_tags))
            .group_by(Hashtag.tag, Post.profile_id)
        )
        sov_results = (await self.db.execute(sov_stmt)).all()

        sov_data = []
        for tag in top_tags:
            tag_rows = [r for r in sov_results if r.tag == tag]
            total_freq = sum(r.freq for r in tag_rows)
            distribution = {}
            for r in tag_rows:
                pct = round((r.freq / total_freq) * 100, 2) if total_freq > 0 else 0
                distribution[str(r.profile_id)] = pct
            
            sov_data.append({
                "tag": tag,
                "distribution": distribution
            })

        return sov_data
