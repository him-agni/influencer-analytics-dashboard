"""
Data transformation service.
Converts raw YouTube API data into structured formats for database storage.
"""

import re
from collections import Counter
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.core.logging import logger


class DataTransformer:
    """Transforms raw API data into database-ready structures."""

    # ── Hashtag Extraction ────────────────────────────────────

    @staticmethod
    def extract_hashtags(text: str) -> list[str]:
        """
        Extract hashtags from text (title + description).
        Returns lowercase, deduplicated list.
        """
        if not text:
            return []
        tags = re.findall(r"#(\w+)", text.lower())
        return list(dict.fromkeys(tags))  # dedupe preserving order

    @staticmethod
    def count_hashtags(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Count hashtag frequency across all videos.
        Returns list of {tag, frequency} sorted by frequency descending.
        """
        counter: Counter = Counter()
        for video in videos:
            text = f"{video.get('title', '')} {video.get('description', '')}"
            tags = re.findall(r"#(\w+)", text.lower())
            counter.update(tags)

        return [
            {"tag": tag, "frequency": freq}
            for tag, freq in counter.most_common()
        ]

    # ── Engagement Calculations ───────────────────────────────

    @staticmethod
    def calculate_engagement_rate(likes: int, comments: int, views: int) -> float:
        """Calculate engagement rate: (likes + comments) / views × 100."""
        if views == 0:
            return 0.0
        return round(((likes + comments) / views) * 100, 4)

    @staticmethod
    def calculate_engagement_metrics(
        videos: list[dict[str, Any]], profile_id: int
    ) -> dict[str, Any]:
        """
        Calculate aggregated engagement metrics from a list of videos.

        Returns dict with: profile_id, date, engagement_rate, avg_likes,
        avg_comments, avg_views, total_posts
        """
        if not videos:
            return {
                "profile_id": profile_id,
                "date": date.today(),
                "engagement_rate": 0.0,
                "avg_likes": 0.0,
                "avg_comments": 0.0,
                "avg_views": 0.0,
                "total_posts": 0,
            }

        df = pd.DataFrame(videos)

        total_likes = df["likes"].sum()
        total_comments = df["comments_count"].sum()
        total_views = df["views"].sum()

        eng_rate = 0.0
        if total_views > 0:
            eng_rate = round(((total_likes + total_comments) / total_views) * 100, 4)

        return {
            "profile_id": profile_id,
            "date": date.today(),
            "engagement_rate": eng_rate,
            "avg_likes": round(df["likes"].mean(), 2),
            "avg_comments": round(df["comments_count"].mean(), 2),
            "avg_views": round(df["views"].mean(), 2),
            "total_posts": len(videos),
        }

    # ── Growth Snapshots ──────────────────────────────────────

    @staticmethod
    def create_growth_snapshot(
        profile_id: int, subscribers: int, total_views: int, video_count: int
    ) -> dict[str, Any]:
        """Create a follower growth snapshot for the current moment."""
        return {
            "profile_id": profile_id,
            "subscribers": subscribers,
            "total_views": total_views,
            "video_count": video_count,
            "timestamp": datetime.utcnow(),
        }

    # ── Video DataFrame Helpers ───────────────────────────────

    @staticmethod
    def videos_to_dataframe(videos: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert raw video list to a Pandas DataFrame with computed columns."""
        if not videos:
            return pd.DataFrame()

        df = pd.DataFrame(videos)

        # Add engagement rate column
        df["engagement_rate"] = df.apply(
            lambda row: DataTransformer.calculate_engagement_rate(
                row.get("likes", 0),
                row.get("comments_count", 0),
                row.get("views", 0),
            ),
            axis=1,
        )

        # Parse published_at for time-based analysis
        if "published_at" in df.columns:
            df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
            df["day_of_week"] = df["published_at"].dt.day_name()
            df["hour"] = df["published_at"].dt.hour
            df["month"] = df["published_at"].dt.to_period("M")

        logger.info(f"Transformed {len(df)} videos to DataFrame")
        return df

    @staticmethod
    def get_posting_heatmap(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Generate posting heatmap data: best days/times to post.
        Returns list of {day_of_week, hour, count, avg_engagement_rate}.
        """
        df = DataTransformer.videos_to_dataframe(videos)
        if df.empty:
            return []

        grouped = (
            df.groupby(["day_of_week", "hour"])
            .agg(
                count=("video_id", "count"),
                avg_engagement_rate=("engagement_rate", "mean"),
            )
            .reset_index()
        )

        return grouped.to_dict(orient="records")

    @staticmethod
    def get_content_type_breakdown(
        videos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Break down performance by content type (video, short, long_form).
        Returns list of {content_type, count, avg_views, avg_likes, avg_engagement_rate}.
        """
        df = DataTransformer.videos_to_dataframe(videos)
        if df.empty:
            return []

        grouped = (
            df.groupby("content_type")
            .agg(
                count=("video_id", "count"),
                avg_views=("views", "mean"),
                avg_likes=("likes", "mean"),
                avg_engagement_rate=("engagement_rate", "mean"),
            )
            .reset_index()
        )

        return grouped.to_dict(orient="records")
