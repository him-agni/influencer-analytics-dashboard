"""
Data collection endpoint — triggers YouTube data pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.logging import logger
from app.repositories.profile_repo import ProfileRepository
from app.repositories.post_repo import PostRepository
from app.schemas.schemas import CollectRequest, CollectResponse
from app.services.youtube_collector import YouTubeCollector
from app.services.data_transformer import DataTransformer
from app.services.sentiment_analyzer import sentiment_analyzer

router = APIRouter(prefix="/collect", tags=["Data Collection"])
settings = get_settings()


@router.post("", response_model=CollectResponse)
async def collect_channel_data(
    request: CollectRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Collect YouTube channel data from a URL or @handle.
    Fetches profile, videos, comments, hashtags, and runs sentiment analysis.
    """
    if not settings.youtube_api_key:
        raise HTTPException(status_code=500, detail="YouTube API key not configured")

    platform = YouTubeCollector.detect_platform(request.url)
    if platform != "youtube":
        raise HTTPException(status_code=400, detail=f"Only YouTube URLs are supported. Detected: {platform}")

    try:
        collector = YouTubeCollector()
        transformer = DataTransformer()
        profile_repo = ProfileRepository(db)
        post_repo = PostRepository(db)

        # 1. Collect channel data
        logger.info(f"Collecting data for: {request.url}")
        channel_data = await collector.collect_channel_data(request.url)
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")

        # 2. Upsert profile
        profile = await profile_repo.upsert({
            "platform": "youtube",
            "channel_id": channel_data["channel_id"],
            "username": channel_data["username"],
            "display_name": channel_data["display_name"],
            "url": channel_data["url"],
            "profile_image_url": channel_data.get("profile_image_url"),
            "banner_image_url": channel_data.get("banner_image_url"),
            "subscribers": channel_data["subscribers"],
            "total_views": channel_data["total_views"],
            "video_count": channel_data["video_count"],
            "bio": channel_data.get("bio"),
            "country": channel_data.get("country"),
            "created_at": channel_data.get("created_at"),
        })

        # 3. Add growth snapshot
        await profile_repo.add_growth_snapshot(
            transformer.create_growth_snapshot(
                profile.id, channel_data["subscribers"],
                channel_data["total_views"], channel_data["video_count"],
            )
        )

        # 4. Collect videos
        videos_data = await collector.collect_videos(
            channel_data["channel_id"], max_results=settings.max_videos_per_channel
        )

        total_comments = 0
        for video_data in videos_data:
            post = await post_repo.upsert({
                "profile_id": profile.id,
                "video_id": video_data["video_id"],
                "title": video_data["title"],
                "url": video_data["url"],
                "thumbnail_url": video_data.get("thumbnail_url"),
                "description": video_data.get("description"),
                "content_type": video_data.get("content_type"),
                "duration": video_data.get("duration"),
                "likes": video_data["likes"],
                "comments_count": video_data["comments_count"],
                "views": video_data["views"],
                "favorites": video_data.get("favorites", 0),
                "published_at": video_data.get("published_at"),
            })

            # Extract hashtags
            text = f"{video_data.get('title', '')} {video_data.get('description', '')}"
            tags = transformer.extract_hashtags(text)
            for tag in tags:
                await post_repo.upsert_hashtag(post.id, tag)

            # Collect comments (top 5 videos only to save API quota)
            if videos_data.index(video_data) < 5:
                comments_data = await collector.collect_comments(
                    video_data["video_id"], max_results=settings.max_comments_per_video
                )
                # Run sentiment analysis
                comments_data = sentiment_analyzer.analyze_comments(comments_data)

                for comment_data in comments_data:
                    await post_repo.upsert_comment({
                        "post_id": post.id,
                        "comment_id": comment_data["comment_id"],
                        "text": comment_data["text"],
                        "author": comment_data.get("author"),
                        "author_channel_id": comment_data.get("author_channel_id"),
                        "likes": comment_data.get("likes", 0),
                        "reply_count": comment_data.get("reply_count", 0),
                        "sentiment_score": comment_data.get("sentiment_score"),
                        "sentiment_label": comment_data.get("sentiment_label"),
                        "posted_at": comment_data.get("posted_at"),
                    })
                    total_comments += 1

        # 5. Calculate engagement metrics
        eng_metrics = transformer.calculate_engagement_metrics(videos_data, profile.id)
        await profile_repo.add_engagement_metric(eng_metrics)

        logger.info(
            f"Collection complete: {profile.display_name} — "
            f"{len(videos_data)} videos, {total_comments} comments"
        )

        return CollectResponse(
            status="success",
            message=f"Collected data for {profile.display_name}",
            profile_id=profile.id,
            videos_collected=len(videos_data),
            comments_collected=total_comments,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
