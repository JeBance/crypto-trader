"""
Crypto Trader - Main Application Entry Point

Usage:
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Environment variables:
    HOST - Server host (default: 0.0.0.0)
    PORT - Server port (default: 8000)
    APP_ENV - Environment (development/production)
    APP_DEBUG - Debug mode (true/false)
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.logger import setup_logger
from app.database import init_db
from app.plugins.manager import PluginManager
from app.plugins.base import ExchangePlugin, StrategyPlugin, NotifierPlugin
from app.core.events import event_bus, EventType, publish
from app.websocket.manager import ws_manager

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)


# Global application state
class AppState:
    """Application state container."""
    
    def __init__(self):
        self.plugin_manager: PluginManager | None = None
        self.exchange: ExchangePlugin | None = None
        self.notifier: NotifierPlugin | None = None
        self.strategy_executor = None
        self.data_service = None
        self.db_session = None


app_state = AppState()


async def initialize_plugins() -> None:
    """Initialize all plugins from configuration."""
    logger.info("Initializing plugins...")
    
    plugin_manager = PluginManager()
    
    # Load exchange plugins
    if settings.BINANCE_API_KEY:
        try:
            from app.exchanges.binance import BinanceExchange
            exchange = BinanceExchange(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_API_SECRET,
                testnet=settings.BINANCE_TESTNET,
            )
            await exchange.initialize()
            plugin_manager.register(exchange)
            logger.info("Binance exchange initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Binance: {e}")
    
    if settings.BYBIT_API_KEY:
        try:
            from app.exchanges.bybit import BybitExchange
            exchange = BybitExchange(
                api_key=settings.BYBIT_API_KEY,
                api_secret=settings.BYBIT_API_SECRET,
                testnet=settings.BYBIT_TESTNET,
            )
            await exchange.initialize()
            plugin_manager.register(exchange)
            logger.info("Bybit exchange initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bybit: {e}")
    
    # Load strategy plugins
    try:
        from app.strategies.rsi import RSIStrategy
        rsi_strategy = RSIStrategy(
            period=14,
            oversold=30,
            overbought=70,
        )
        await rsi_strategy.initialize()
        plugin_manager.register(rsi_strategy)
        logger.info("RSI strategy initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RSI strategy: {e}")
    
    # Load notifier plugins
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.notifications.telegram import TelegramNotifier
            notifier = TelegramNotifier(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.TELEGRAM_CHAT_ID,
            )
            await notifier.initialize()
            plugin_manager.register(notifier)
            logger.info("Telegram notifier initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram notifier: {e}")
    
    # Store in app state
    app_state.plugin_manager = plugin_manager
    
    # Set primary exchange and notifier
    if plugin_manager.exchange_plugins:
        app_state.exchange = list(plugin_manager.exchange_plugins.values())[0]
    
    if plugin_manager.notifier_plugins:
        app_state.notifier = list(plugin_manager.notifier_plugins.values())[0]
    
    logger.info(f"Initialized {len(plugin_manager.all_plugins)} plugins")


async def initialize_services() -> None:
    """Initialize core services."""
    logger.info("Initializing services...")
    
    if app_state.exchange:
        # Initialize Data Service
        from app.services.data_service import DataService
        app_state.data_service = DataService(app_state.exchange)
        logger.info("Data Service initialized")
        
        # Initialize Strategy Executor
        from app.services.strategy_executor import StrategyExecutor
        app_state.strategy_executor = StrategyExecutor(
            exchange=app_state.exchange,
            plugin_manager=app_state.plugin_manager,
            notifier=app_state.notifier,
        )
        await app_state.strategy_executor.start()
        logger.info("Strategy Executor initialized")


async def cleanup_plugins() -> None:
    """Cleanup all plugins on shutdown."""
    logger.info("Cleaning up plugins...")
    
    if app_state.strategy_executor:
        await app_state.strategy_executor.stop()
    
    if app_state.plugin_manager:
        await app_state.plugin_manager.shutdown_all()
    
    logger.info("Cleanup complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Crypto Trader starting up...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize plugins
        await initialize_plugins()
        
        # Initialize services
        await initialize_services()
        
        # Publish system started event
        await publish(
            EventType.SYSTEM_STARTED,
            {"version": "0.1.0"},
            source="main",
        )
        
        logger.info("✅ Crypto Trader ready!")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Crypto Trader shutting down...")
    
    await publish(
        EventType.SYSTEM_STOPPED,
        {},
        source="main",
    )
    
    await cleanup_plugins()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Crypto Trader",
        description="Automated cryptocurrency trading system for Termux on Android",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from app.api.health import router as health_router
    from app.api.config import router as config_router
    from app.api.orders import router as orders_router
    from app.api.positions import router as positions_router
    from app.api.strategies import router as strategies_router
    from app.websocket.routes import router as websocket_router
    
    app.include_router(health_router)
    app.include_router(config_router)
    app.include_router(orders_router)
    app.include_router(positions_router)
    app.include_router(strategies_router)
    app.include_router(websocket_router)
    
    # Mount static files (for frontend)
    static_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
        logger.info(f"Static files mounted from {static_path}")
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Crypto Trader",
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
        }
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_DEBUG,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )
