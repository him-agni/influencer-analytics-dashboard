"""
Scheduled background jobs for automated data refresh.
Uses APScheduler with AsyncIOScheduler.
"""

from app.core.config import get_settings
from app.core.logging import logger
from app.database import async_session
from app.repositories.profile_repo import ProfileRepository
from app.services.youtube_collector import YouTubeCollector
from app.services.data_transformer import DataTransformer

settings = get_settings()


async def refresh_all_profiles():
    """
    Re-collect stats for all tracked profiles.
    Runs on schedule to keep data fresh.
    """
    if not settings.youtube_api_key:
        logger.warning("Skipping refresh: YouTube API key not configured")
        return

    logger.info("Starting scheduled profile refresh...")

    try:
        collector = YouTubeCollector()
        transformer = DataTransformer()

        async with async_session() as session:
            async with session.begin():
                repo = ProfileRepository(session)
                profiles = await repo.get_all(limit=100)

                for profile in profiles:
                    try:
                        # Re-fetch channel stats
                        data = await collector.collect_channel_data(profile.url)
                        if not data:
                            continue

                        # Update profile
                        await repo.upsert({
                            "channel_id": data["channel_id"],
                            "subscribers": data["subscribers"],
                            "total_views": data["total_views"],
                            "video_count": data["video_count"],
                        })

                        # Add growth snapshot
                        await repo.add_growth_snapshot(
                            transformer.create_growth_snapshot(
                                profile.id, data["subscribers"],
                                data["total_views"], data["video_count"],
                            )
                        )

                        logger.info(f"Refreshed: {profile.display_name}")
                    except Exception as e:
                        logger.error(f"Error refreshing {profile.username}: {e}")

        logger.info("Scheduled refresh complete")
    except Exception as e:
        logger.error(f"Refresh job failed: {e}")
