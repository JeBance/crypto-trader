"""Database configuration and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_session
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


# SQLAlchemy 1.4.x compatibility
Base = declarative_base()


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set True for SQL logging
    future=True,
)

# Create async session factory (SQLAlchemy 1.4.x compatibility)
def make_session():
    """Create async session."""
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

AsyncSessionLocal = make_session()


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import candle, order, position, trade, market_data  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
