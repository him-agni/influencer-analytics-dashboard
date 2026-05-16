"""Pydantic schemas for API request/response models."""

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────

class CollectRequest(BaseModel):
    url: str = Field(..., description="YouTube channel URL or @handle")


# ── Profile Schemas ───────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: int
    platform: str
    channel_id: str
    username: str
    display_name: Optional[str] = None
    url: str
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    subscribers: int = 0
    total_views: int = 0
    video_count: int = 0
    bio: Optional[str] = None
    country: Optional[str] = None
    created_at: Optional[datetime] = None
    fetched_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Post Schemas ──────────────────────────────────────────────

class PostResponse(BaseModel):
    id: int
    video_id: str
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    content_type: Optional[str] = None
    likes: int = 0
    comments_count: int = 0
    views: int = 0
    duration: Optional[str] = None
    published_at: Optional[datetime] = None
    engagement_rate: float = 0.0

    class Config:
        from_attributes = True


# ── Comment Schemas ───────────────────────────────────────────

class CommentResponse(BaseModel):
    id: int
    text: str
    author: Optional[str] = None
    likes: int = 0
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Analytics Schemas ─────────────────────────────────────────

class GrowthPointResponse(BaseModel):
    subscribers: int
    total_views: int
    video_count: int
    timestamp: datetime

    class Config:
        from_attributes = True


class EngagementResponse(BaseModel):
    date: date
    engagement_rate: float
    avg_likes: float
    avg_comments: float
    avg_views: float
    total_posts: int

    class Config:
        from_attributes = True


class HashtagResponse(BaseModel):
    tag: str
    frequency: int


class CategoryDistribution(BaseModel):
    category: str
    percentage: float


class SentimentSummary(BaseModel):
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    neutral_pct: float = 0.0
    avg_score: float = 0.0


class ScoreBreakdown(BaseModel):
    score: float
    weight: float
    raw_value: float


class InfluenceScoreResponse(BaseModel):
    overall_score: float
    tier: str
    breakdown: dict[str, ScoreBreakdown]


class CollectResponse(BaseModel):
    status: str
    message: str
    profile_id: Optional[int] = None
    videos_collected: int = 0
    comments_collected: int = 0


class DashboardSummary(BaseModel):
    total_profiles: int = 0
    total_videos: int = 0
    total_comments: int = 0
    profiles: list[ProfileResponse] = []


class CompareRequest(BaseModel):
    profile_ids: list[int]


class SOVData(BaseModel):
    tag: str
    distribution: dict[str, float]


class CompareProfileStats(BaseModel):
    profile_id: int
    display_name: str
    username: str
    subscribers: int
    total_views: int
    video_count: int
    engagement_rate: float
    influence_score: float


class CompareResponse(BaseModel):
    profiles: list[CompareProfileStats]
    benchmark_engagement_rate: float
    sov_data: list[SOVData]


class ViralPost(BaseModel):
    post_id: int
    video_id: str
    title: str
    views: int
    expected_views: int
    multiplier: float
    published_at: Optional[str] = None


class Spike(BaseModel):
    date: str
    old_subscribers: int
    new_subscribers: int
    percentage_jump: float


class FollowerDrop(BaseModel):
    date: str
    old_subscribers: int
    new_subscribers: int
    lost_count: int
    percentage_drop: float


class AnomalyResponse(BaseModel):
    viral_posts: list[ViralPost]
    suspicious_growth_spikes: list[Spike]
    follower_drops: list[FollowerDrop]
    fake_follower_risk: str
    fake_follower_flags: list[str]
