"""
Profile and analytics API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.profile_repo import ProfileRepository
from app.repositories.post_repo import PostRepository
from app.schemas.schemas import (
    ProfileResponse, PostResponse, CommentResponse, GrowthPointResponse,
    EngagementResponse, HashtagResponse, InfluenceScoreResponse,
    SentimentSummary, DashboardSummary, CategoryDistribution,
    CompareRequest, CompareResponse, CompareProfileStats, SOVData, AnomalyResponse,
)
from app.services.scoring import influence_scorer
from app.services.sentiment_analyzer import sentiment_analyzer
from app.services.category_classifier import category_classifier
from app.services.anomaly_detector import anomaly_detector

router = APIRouter(tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary with all profiles."""
    repo = ProfileRepository(db)
    post_repo = PostRepository(db)
    
    profiles = await repo.get_all()
    total_videos = await post_repo.count_posts()
    total_comments = await post_repo.count_comments()
    
    return DashboardSummary(
        total_profiles=len(profiles),
        total_videos=total_videos,
        total_comments=total_comments,
        profiles=[ProfileResponse.model_validate(p) for p in profiles],
    )


@router.get("/profiles", response_model=list[ProfileResponse])
async def list_profiles(
    skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)
):
    repo = ProfileRepository(db)
    profiles = await repo.get_all(skip=skip, limit=limit)
    return [ProfileResponse.model_validate(p) for p in profiles]


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    repo = ProfileRepository(db)
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse.model_validate(profile)


@router.get("/profiles/{profile_id}/posts", response_model=list[PostResponse])
async def get_posts(
    profile_id: int,
    skip: int = 0, limit: int = 50,
    sort_by: str = Query("published_at", enum=["published_at", "views", "likes", "comments_count"]),
    db: AsyncSession = Depends(get_db),
):
    repo = PostRepository(db)
    posts = await repo.get_by_profile(profile_id, skip=skip, limit=limit, sort_by=sort_by)
    results = []
    for p in posts:
        data = PostResponse.model_validate(p)
        data.engagement_rate = p.engagement_rate
        results.append(data)
    return results


@router.get("/profiles/{profile_id}/growth", response_model=list[GrowthPointResponse])
async def get_growth(
    profile_id: int, limit: int = 365, db: AsyncSession = Depends(get_db)
):
    repo = ProfileRepository(db)
    snapshots = await repo.get_growth_history(profile_id, limit=limit)
    return [GrowthPointResponse.model_validate(s) for s in snapshots]


@router.get("/profiles/{profile_id}/engagement", response_model=list[EngagementResponse])
async def get_engagement(
    profile_id: int, limit: int = 365, db: AsyncSession = Depends(get_db)
):
    repo = ProfileRepository(db)
    metrics = await repo.get_engagement_history(profile_id, limit=limit)
    return [EngagementResponse.model_validate(m) for m in metrics]


@router.get("/profiles/{profile_id}/hashtags", response_model=list[HashtagResponse])
async def get_hashtags(
    profile_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    repo = PostRepository(db)
    return await repo.get_top_hashtags(profile_id, limit=limit)


@router.get("/profiles/{profile_id}/categories", response_model=list[CategoryDistribution])
async def get_categories(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile_repo = ProfileRepository(db)
    post_repo = PostRepository(db)

    profile = await profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    posts = await post_repo.get_by_profile(profile_id, limit=50)
    
    distribution = category_classifier.analyze_profile_categories(profile, posts)
    return [CategoryDistribution(**item) for item in distribution]


@router.get("/profiles/{profile_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    profile_id: int, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    repo = PostRepository(db)
    comments = await repo.get_comments_by_profile(profile_id, limit=limit)
    return [CommentResponse.model_validate(c) for c in comments]


@router.get("/profiles/{profile_id}/sentiment", response_model=SentimentSummary)
async def get_sentiment(profile_id: int, db: AsyncSession = Depends(get_db)):
    repo = PostRepository(db)
    comments = await repo.get_comments_by_profile(profile_id, limit=1000)
    comment_dicts = [
        {"sentiment_label": c.sentiment_label, "sentiment_score": c.sentiment_score}
        for c in comments
    ]
    return sentiment_analyzer.get_sentiment_summary(comment_dicts)


@router.get("/profiles/{profile_id}/score", response_model=InfluenceScoreResponse)
async def get_influence_score(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile_repo = ProfileRepository(db)
    post_repo = PostRepository(db)

    profile = await profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get engagement metrics
    metrics = await profile_repo.get_engagement_history(profile_id, limit=1)
    eng_rate = metrics[0].engagement_rate if metrics else 0.0

    # Get growth rate (compare last two snapshots)
    growth = await profile_repo.get_growth_history(profile_id, limit=2)
    growth_rate = 0.0
    if len(growth) >= 2 and growth[1].subscribers > 0:
        growth_rate = ((growth[0].subscribers - growth[1].subscribers) / growth[1].subscribers) * 100

    # Posts per month estimate
    posts = await post_repo.get_by_profile(profile_id, limit=30)
    posts_per_month = len(posts)  # rough estimate from recent data

    # Sentiment
    comments = await post_repo.get_comments_by_profile(profile_id, limit=500)
    pos_pct = 50.0
    if comments:
        pos = sum(1 for c in comments if c.sentiment_label == "POSITIVE")
        pos_pct = (pos / len(comments)) * 100

    result = influence_scorer.compute_score(
        subscribers=profile.subscribers,
        engagement_rate=eng_rate,
        growth_rate=growth_rate,
        posts_per_month=posts_per_month,
        positive_sentiment_pct=pos_pct,
    )
    return result


@router.post("/compare", response_model=CompareResponse)
async def compare_profiles(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    profile_repo = ProfileRepository(db)
    post_repo = PostRepository(db)

    benchmark_eng_rate = await post_repo.get_average_engagement_rate()

    profiles_stats = []
    for pid in request.profile_ids:
        profile = await profile_repo.get_by_id(pid)
        if not profile:
            continue
            
        eng_history = await profile_repo.get_engagement_history(pid, limit=1)
        eng_rate = eng_history[0].engagement_rate if eng_history else 0.0

        growth = await profile_repo.get_growth_history(pid, limit=2)
        growth_rate = 0.0
        if len(growth) >= 2 and growth[1].subscribers > 0:
            growth_rate = ((growth[0].subscribers - growth[1].subscribers) / growth[1].subscribers) * 100

        posts = await post_repo.get_by_profile(pid, limit=30)
        posts_per_month = len(posts)

        comments = await post_repo.get_comments_by_profile(pid, limit=50)
        pos_pct = 50.0
        if comments:
            pos = sum(1 for c in comments if c.sentiment_label == "POSITIVE")
            pos_pct = (pos / len(comments)) * 100

        score_res = influence_scorer.compute_score(
            subscribers=profile.subscribers,
            engagement_rate=eng_rate,
            growth_rate=growth_rate,
            posts_per_month=posts_per_month,
            positive_sentiment_pct=pos_pct,
        )

        profiles_stats.append(CompareProfileStats(
            profile_id=profile.id,
            display_name=profile.display_name or profile.username,
            username=profile.username,
            subscribers=profile.subscribers,
            total_views=profile.total_views,
            video_count=profile.video_count,
            engagement_rate=eng_rate,
            influence_score=score_res["overall_score"]
        ))

    sov_data_raw = await post_repo.get_hashtag_sov(request.profile_ids, limit=15)
    sov_data = [SOVData(**item) for item in sov_data_raw]

    return CompareResponse(
        profiles=profiles_stats,
        benchmark_engagement_rate=benchmark_eng_rate,
        sov_data=sov_data
    )


@router.get("/profiles/{profile_id}/anomalies", response_model=AnomalyResponse)
async def get_anomalies(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile_repo = ProfileRepository(db)
    post_repo = PostRepository(db)

    profile = await profile_repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    posts = await post_repo.get_by_profile(profile_id, limit=50)
    growth_history = await profile_repo.get_growth_history(profile_id, limit=30)
    
    eng_history = await profile_repo.get_engagement_history(profile_id, limit=1)
    eng_rate = eng_history[0].engagement_rate if eng_history else 0.0

    analysis = anomaly_detector.analyze_profile(profile, posts, growth_history, eng_rate)
    return AnomalyResponse(**analysis)
