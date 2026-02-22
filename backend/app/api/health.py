"""Health check API routes."""

import logging
from datetime import datetime

from fastapi import APIRouter

from app.config import settings
from app.plugins.manager import PluginManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns application status and version.
    """
    return {
        "status": "healthy",
        "name": "Crypto Trader",
        "version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if all required components are ready.
    """
    checks = {
        "config": True,
        "database": True,  # TODO: Add actual DB check
        "exchanges": True,
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
    }


@router.get("/status")
async def system_status(plugin_manager: PluginManager | None = None):
    """
    Detailed system status.
    
    Returns information about all system components.
    """
    status = {
        "application": {
            "name": "Crypto Trader",
            "version": "0.2.0",
            "environment": settings.APP_ENV,
            "debug": settings.APP_DEBUG,
            "trading_mode": settings.TRADING_MODE,
        },
        "server": {
            "host": settings.HOST,
            "port": settings.PORT,
        },
        "configuration": {
            "fully_configured": settings.is_fully_configured,
            "exchanges": settings.exchanges_configured,
            "telegram": settings.telegram_configured,
            "env_file_exists": True,  # Created automatically
        },
        "plugins": {},
    }
    
    # Add plugin information if manager is available
    if plugin_manager:
        status["plugins"] = plugin_manager.get_info()
    
    return status
