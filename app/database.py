"""
SQLAlchemy async engine and session configuration.
Supports both SQLite (aiosqlite) and PostgreSQL (asyncpg).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# ── Railway compatibility ─────────────────────────────────────
# Railway provides DATABASE_URL as "postgresql://..." but asyncpg needs "postgresql+asyncpg://..."
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# ── Engine Configuration ──────────────────────────────────────
# SQLite needs connect_args for check_same_thread
if settings.is_sqlite:
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# ── Session Factory ───────────────────────────────────────────
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative Base ──────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Lifecycle Helpers ─────────────────────────────────────────
async def create_tables():
    """Create all tables (for development / SQLite). Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables (for testing only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
