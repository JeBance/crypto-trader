"""
Crypto Trader - Main Application Entry Point

Usage:
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logger import setup_logger
from app.database import init_db

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Crypto Trader starting up...")
    await init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Crypto Trader shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Crypto Trader",
        description="Automated cryptocurrency trading system",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Crypto Trader",
            "version": "0.1.0",
            "status": "running",
        }
    
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "database": "connected",
        }
    
    # TODO: Include routers
    # app.include_router(health_router, prefix="/api")
    # app.include_router(orders_router, prefix="/api/orders")
    # app.include_router(positions_router, prefix="/api/positions")
    # app.include_router(strategies_router, prefix="/api/strategies")
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_DEBUG,
    )
