"""
YouTube Data API v3 collector service.
Handles channel info, videos, and comments collection.
"""

import re
from datetime import datetime
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class YouTubeCollector:
    """Collects data from YouTube Data API v3."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.youtube_api_key
        if not self.api_key:
            raise ValueError(
                "YouTube API key is required. Set YOUTUBE_API_KEY in your .env file. "
                "Get one at: https://console.cloud.google.com/apis/credentials"
            )
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    # ── URL Parsing ───────────────────────────────────────────

    @staticmethod
    def parse_channel_identifier(url_or_id: str) -> dict[str, str]:
        """
        Parse a YouTube URL or ID into a lookup method and value.

        Supports:
          - https://youtube.com/@username
          - https://youtube.com/channel/UC...
          - https://youtube.com/c/customname
          - https://youtube.com/user/username
          - Raw channel ID (UC...)
          - Raw @username
        """
        url_or_id = url_or_id.strip()

        # @handle format (with or without URL)
        handle_match = re.search(r"@([\w.-]+)", url_or_id)
        if handle_match:
            return {"type": "handle", "value": f"@{handle_match.group(1)}"}

        # /channel/UC... format
        channel_match = re.search(r"/channel/(UC[\w-]+)", url_or_id)
        if channel_match:
            return {"type": "channel_id", "value": channel_match.group(1)}

        # /c/customname or /user/username format
        custom_match = re.search(r"/(c|user)/([\w.-]+)", url_or_id)
        if custom_match:
            return {"type": "custom_url", "value": custom_match.group(2)}

        # Raw channel ID (starts with UC)
        if url_or_id.startswith("UC") and len(url_or_id) == 24:
            return {"type": "channel_id", "value": url_or_id}

        # Fallback: treat as search query
        return {"type": "search", "value": url_or_id}

    @staticmethod
    def detect_platform(url: str) -> str:
        """Detect platform from URL (future-proofing for Instagram)."""
        url = url.lower()
        if "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        elif "instagram.com" in url:
            return "instagram"
        else:
            return "unknown"

    # ── Channel Data ──────────────────────────────────────────

    async def get_channel_id(self, identifier: dict[str, str]) -> Optional[str]:
        """Resolve any identifier type to a channel ID."""
        try:
            id_type = identifier["type"]
            value = identifier["value"]

            if id_type == "channel_id":
                return value

            if id_type == "handle":
                # Use forHandle parameter (added in 2023)
                request = self.youtube.channels().list(
                    part="id",
                    forHandle=value.lstrip("@"),
                )
                response = request.execute()
                if response.get("items"):
                    return response["items"][0]["id"]

            if id_type == "custom_url":
                # Search for the channel
                request = self.youtube.search().list(
                    part="snippet",
                    q=value,
                    type="channel",
                    maxResults=1,
                )
                response = request.execute()
                if response.get("items"):
                    return response["items"][0]["snippet"]["channelId"]

            if id_type == "search":
                request = self.youtube.search().list(
                    part="snippet",
                    q=value,
                    type="channel",
                    maxResults=1,
                )
                response = request.execute()
                if response.get("items"):
                    return response["items"][0]["snippet"]["channelId"]

        except HttpError as e:
            logger.error(f"YouTube API error resolving channel: {e}")
            raise

        return None

    async def collect_channel_data(self, url_or_id: str) -> Optional[dict[str, Any]]:
        """
        Collect full channel profile data from a URL or ID.

        Returns dict with: channel_id, username, display_name, url, subscribers,
        total_views, video_count, bio, profile_image_url, banner_image_url,
        country, created_at
        """
        identifier = self.parse_channel_identifier(url_or_id)
        channel_id = await self.get_channel_id(identifier)

        if not channel_id:
            logger.warning(f"Could not resolve channel: {url_or_id}")
            return None

        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,brandingSettings",
                id=channel_id,
            )
            response = request.execute()

            if not response.get("items"):
                return None

            channel = response["items"][0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})
            branding = channel.get("brandingSettings", {})

            # Parse channel creation date
            created_at = None
            if snippet.get("publishedAt"):
                created_at = datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ).replace(tzinfo=None)

            # Get best quality thumbnail
            thumbnails = snippet.get("thumbnails", {})
            profile_image = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            # Banner image from branding
            banner_url = branding.get("image", {}).get("bannerExternalUrl")

            return {
                "channel_id": channel_id,
                "username": snippet.get("customUrl", "").lstrip("@") or channel_id,
                "display_name": snippet.get("title", ""),
                "url": f"https://youtube.com/channel/{channel_id}",
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "bio": snippet.get("description", ""),
                "profile_image_url": profile_image,
                "banner_image_url": banner_url,
                "country": snippet.get("country"),
                "created_at": created_at,
            }

        except HttpError as e:
            logger.error(f"YouTube API error collecting channel data: {e}")
            raise

    # ── Videos ────────────────────────────────────────────────

    async def collect_videos(
        self, channel_id: str, max_results: int = 50
    ) -> list[dict[str, Any]]:
        """
        Collect recent videos for a channel.

        Returns list of dicts with: video_id, title, url, thumbnail_url,
        description, likes, comments_count, views, favorites, duration,
        content_type, published_at
        """
        video_ids = []

        try:
            # Step 1: Get video IDs via search
            page_token = None
            while len(video_ids) < max_results:
                request = self.youtube.search().list(
                    part="id",
                    channelId=channel_id,
                    type="video",
                    order="date",
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=page_token,
                )
                response = request.execute()

                for item in response.get("items", []):
                    video_ids.append(item["id"]["videoId"])

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            if not video_ids:
                return []

            # Step 2: Get full video details in batches of 50
            videos = []
            for i in range(0, len(video_ids), 50):
                batch = video_ids[i : i + 50]
                request = self.youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(batch),
                )
                response = request.execute()

                for item in response.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    content = item.get("contentDetails", {})

                    # Parse published date
                    published_at = None
                    if snippet.get("publishedAt"):
                        published_at = datetime.fromisoformat(
                            snippet["publishedAt"].replace("Z", "+00:00")
                        ).replace(tzinfo=None)

                    # Determine content type from duration
                    duration = content.get("duration", "")
                    content_type = self._classify_content_type(duration)

                    # Best thumbnail
                    thumbnails = snippet.get("thumbnails", {})
                    thumbnail = (
                        thumbnails.get("high", {}).get("url")
                        or thumbnails.get("medium", {}).get("url")
                        or thumbnails.get("default", {}).get("url")
                    )

                    videos.append(
                        {
                            "video_id": item["id"],
                            "title": snippet.get("title", ""),
                            "url": f"https://youtube.com/watch?v={item['id']}",
                            "thumbnail_url": thumbnail,
                            "description": snippet.get("description", ""),
                            "likes": int(stats.get("likeCount", 0)),
                            "comments_count": int(stats.get("commentCount", 0)),
                            "views": int(stats.get("viewCount", 0)),
                            "favorites": int(stats.get("favoriteCount", 0)),
                            "duration": duration,
                            "content_type": content_type,
                            "published_at": published_at,
                        }
                    )

            logger.info(f"Collected {len(videos)} videos for channel {channel_id}")
            return videos

        except HttpError as e:
            logger.error(f"YouTube API error collecting videos: {e}")
            raise

    @staticmethod
    def _classify_content_type(iso_duration: str) -> str:
        """
        Classify video type based on ISO 8601 duration.
        Shorts are typically <= 60 seconds.
        """
        # Parse ISO 8601 duration (e.g., PT1M30S, PT15S, PT1H2M3S)
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
        if not match:
            return "video"

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds

        if total_seconds <= 60:
            return "short"
        elif total_seconds >= 3600:
            return "long_form"
        else:
            return "video"

    # ── Comments ──────────────────────────────────────────────

    async def collect_comments(
        self, video_id: str, max_results: int = 100
    ) -> list[dict[str, Any]]:
        """
        Collect top-level comments for a video.

        Returns list of dicts with: comment_id, text, author, author_channel_id,
        likes, reply_count, posted_at
        """
        comments = []

        try:
            page_token = None
            while len(comments) < max_results:
                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    order="relevance",
                    maxResults=min(100, max_results - len(comments)),
                    pageToken=page_token,
                )
                response = request.execute()

                for item in response.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]

                    posted_at = None
                    if snippet.get("publishedAt"):
                        posted_at = datetime.fromisoformat(
                            snippet["publishedAt"].replace("Z", "+00:00")
                        ).replace(tzinfo=None)

                    comments.append(
                        {
                            "comment_id": item["id"],
                            "text": snippet.get("textDisplay", ""),
                            "author": snippet.get("authorDisplayName", ""),
                            "author_channel_id": snippet.get(
                                "authorChannelId", {}
                            ).get("value"),
                            "likes": int(snippet.get("likeCount", 0)),
                            "reply_count": int(
                                item.get("snippet", {}).get("totalReplyCount", 0)
                            ),
                            "posted_at": posted_at,
                        }
                    )

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            logger.info(f"Collected {len(comments)} comments for video {video_id}")
            return comments

        except HttpError as e:
            # Comments may be disabled
            if e.resp.status == 403:
                logger.warning(f"Comments disabled for video {video_id}")
                return []
            logger.error(f"YouTube API error collecting comments: {e}")
            raise
