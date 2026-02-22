"""REST API routes."""

from app.api.health import router as health_router
from app.api.config import router as config_router
from app.api.orders import router as orders_router
from app.api.positions import router as positions_router
from app.api.strategies import router as strategies_router

__all__ = [
    "health_router",
    "config_router",
    "orders_router",
    "positions_router",
    "strategies_router",
]
