"""Database connection and session management."""

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.config import settings


def _asyncpg_engine_url_and_connect_args(url: str) -> tuple[str, dict]:
    """Build asyncpg URL and connect_args (asyncpg does not accept sslmode= in URL)."""
    connect_args: dict = {}
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = (query.get("sslmode") or [""])[0].lower()
    if sslmode == "disable":
        connect_args["ssl"] = False
    filtered = {k: v for k, v in query.items() if k.lower() != "sslmode"}
    new_query = urlencode(filtered, doseq=True)
    cleaned = urlunparse(parsed._replace(query=new_query))
    if cleaned.startswith("postgresql://"):
        cleaned = cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif cleaned.startswith("postgresql+asyncpg://"):
        pass
    else:
        cleaned = cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
    return cleaned, connect_args


database_url, _engine_connect_args = _asyncpg_engine_url_and_connect_args(settings.database_url)

engine = create_async_engine(
    database_url,
    connect_args=_engine_connect_args,
    echo=settings.debug,
    poolclass=NullPool,  # For async, NullPool is recommended
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
