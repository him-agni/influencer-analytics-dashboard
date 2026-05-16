"""
Aggregated v1 API router.
"""

from fastapi import APIRouter
from app.api.v1.collect import router as collect_router
from app.api.v1.profiles import router as profiles_router

router = APIRouter(prefix="/api/v1")
router.include_router(collect_router)
router.include_router(profiles_router)
