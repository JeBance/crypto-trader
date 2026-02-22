"""Configuration API routes."""

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["Configuration"])


class EnvVar(BaseModel):
    """Environment variable model."""
    key: str
    value: str | None = None
    is_secret: bool = False


@router.get("")
async def get_config():
    """
    Get current configuration.
    
    Returns non-sensitive configuration values.
    """
    return {
        "app": {
            "env": settings.APP_ENV,
            "debug": settings.APP_DEBUG,
            "log_level": settings.APP_LOG_LEVEL,
        },
        "server": {
            "host": settings.HOST,
            "port": settings.PORT,
        },
        "trading": {
            "mode": settings.TRADING_MODE,
            "max_position_size_percent": settings.MAX_POSITION_SIZE_PERCENT,
            "stop_loss_percent": settings.STOP_LOSS_PERCENT,
            "take_profit_percent": settings.TAKE_PROFIT_PERCENT,
            "daily_loss_limit_percent": settings.DAILY_LOSS_LIMIT_PERCENT,
        },
        "exchanges": {
            "binance": {
                "configured": bool(settings.BINANCE_API_KEY),
                "testnet": settings.BINANCE_TESTNET,
            },
            "bybit": {
                "configured": bool(settings.BYBIT_API_KEY),
                "testnet": settings.BYBIT_TESTNET,
            },
        },
        "notifications": {
            "telegram": {
                "configured": bool(settings.TELEGRAM_BOT_TOKEN),
            },
        },
    }


@router.get("/env")
async def get_env_vars():
    """
    Get environment variables (non-sensitive only).
    
    Returns list of configured environment variables.
    """
    sensitive_keys = [
        "api_key",
        "api_secret",
        "secret",
        "token",
        "password",
    ]
    
    env_vars = []
    for key in [
        "APP_ENV",
        "APP_DEBUG",
        "APP_LOG_LEVEL",
        "HOST",
        "PORT",
        "TRADING_MODE",
        "BINANCE_TESTNET",
        "BYBIT_TESTNET",
    ]:
        env_vars.append(EnvVar(
            key=key,
            value=str(getattr(settings, key, os.getenv(key, ""))),
            is_secret=False,
        ))
    
    # Add sensitive keys without values
    for key in [
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "TELEGRAM_BOT_TOKEN",
    ]:
        is_configured = bool(getattr(settings, key, os.getenv(key, "")))
        env_vars.append(EnvVar(
            key=key,
            value="***configured***" if is_configured else None,
            is_secret=True,
        ))
    
    return {"variables": env_vars}


@router.get("/exchanges")
async def get_exchange_config():
    """
    Get exchange configurations.
    """
    return {
        "binance": {
            "enabled": bool(settings.BINANCE_API_KEY),
            "testnet": settings.BINANCE_TESTNET,
            "base_url": "https://testnet.binance.vision" if settings.BINANCE_TESTNET else "https://api.binance.com",
        },
        "bybit": {
            "enabled": bool(settings.BYBIT_API_KEY),
            "testnet": settings.BYBIT_TESTNET,
            "base_url": "https://api-testnet.bybit.com" if settings.BYBIT_TESTNET else "https://api.bybit.com",
        },
    }
