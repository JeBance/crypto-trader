"""
Crypto Trader - Main Application Entry Point

Usage:
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Environment variables:
    HOST - Server host (default: 0.0.0.0)
    PORT - Server port (default: 8000)
    APP_ENV - Environment (development/production)
    APP_DEBUG - Debug mode (true/false)

Note: Application works without .env file using default values.
      Configure API keys via Settings page or .env file.
"""

import logging
import os
import signal
from contextlib import asynccontextmanager
from datetime import datetime
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

# Global flag for restart
_restart_requested = False


def handle_sigterm(signum, frame):
    """Handle SIGTERM signal for restart."""
    global _restart_requested
    logger.info("SIGTERM received")
    _restart_requested = True
    # Exit with code 3 for restart
    os._exit(3)


# Register signal handler
signal.signal(signal.SIGTERM, handle_sigterm)


# Global application state
class AppState:
    """Application state container."""

    def __init__(self):
        self.plugin_manager: PluginManager | None = None
        self.exchange: ExchangePlugin | None = None
        self.notifier: NotifierPlugin | None = None
        self.strategy_executor = None
        self.data_service = None
        self.data_collection_manager = None  # NEW: Data collection manager
        self.db_session = None
        self.start_time: datetime | None = None
        self.restart_pending: bool = False
        self.update_pending: bool = False


app_state = AppState()
_startup_time: datetime | None = None


def get_uptime() -> datetime | None:
    """Get application uptime."""
    return _startup_time


def request_restart():
    """Request application restart."""
    app_state.restart_pending = True
    logger.info("Restart requested")


def request_update():
    """Request application update."""
    app_state.update_pending = True
    logger.info("Update requested")


def create_default_env() -> None:
    """Create default .env file if it doesn't exist."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        logger.info("Creating default .env file...")
        
        default_env = """# Crypto Trader Configuration
# Generated automatically - edit to add your API keys

# Application
APP_ENV=development
APP_DEBUG=true
APP_LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/crypto_trader.db

# Security (change in production!)
API_KEY=crypto-trader-default-key-change-in-production
SECRET_KEY=crypto-trader-default-secret-change-in-production

# Trading Mode (paper = demo, live = real)
TRADING_MODE=paper

# Binance API (get from https://www.binance.com/en/my/settings/api-management)
# Leave empty to skip Binance initialization
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=true

# Bybit API (get from https://testnet.bybit.com/app/user/api-management)
# Leave empty to skip Bybit initialization
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_TESTNET=true

# Telegram Bot (get from @BotFather)
# Leave empty to skip Telegram notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Risk Management
MAX_POSITION_SIZE_PERCENT=10
STOP_LOSS_PERCENT=2
TAKE_PROFIT_PERCENT=4
DAILY_LOSS_LIMIT_PERCENT=5
"""
        
        try:
            env_path.write_text(default_env)
            logger.info(f"Created .env file at {env_path}")
        except Exception as e:
            logger.warning(f"Failed to create .env file: {e}")
            logger.warning("Application will use default values")


async def initialize_plugins() -> None:
    """Initialize all plugins from configuration."""
    logger.info("Initializing plugins...")
    
    plugin_manager = PluginManager()
    exchanges_loaded = 0
    
    # Load exchange plugins (only if API keys provided)
    if settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET:
        try:
            from app.exchanges.binance import BinanceExchange
            exchange = BinanceExchange(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_API_SECRET,
                testnet=settings.BINANCE_TESTNET,
            )
            await exchange.initialize()
            plugin_manager.register(exchange)
            logger.info("✅ Binance exchange initialized")
            exchanges_loaded += 1
        except Exception as e:
            logger.error(f"Failed to initialize Binance: {e}")
    else:
        logger.info("⚠️  Binance not configured (API keys not set)")
    
    if settings.BYBIT_API_KEY and settings.BYBIT_API_SECRET:
        try:
            from app.exchanges.bybit import BybitExchange
            exchange = BybitExchange(
                api_key=settings.BYBIT_API_KEY,
                api_secret=settings.BYBIT_API_SECRET,
                testnet=settings.BYBIT_TESTNET,
            )
            await exchange.initialize()
            plugin_manager.register(exchange)
            logger.info("✅ Bybit exchange initialized")
            exchanges_loaded += 1
        except Exception as e:
            logger.error(f"Failed to initialize Bybit: {e}")
    else:
        logger.info("⚠️  Bybit not configured (API keys not set)")
    
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
        logger.info("✅ RSI strategy initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RSI strategy: {e}")
    
    try:
        from app.strategies.crossover import CrossoverStrategy
        crossover_strategy = CrossoverStrategy(
            fast_period=9,
            slow_period=21,
            ma_type="ema",
        )
        await crossover_strategy.initialize()
        plugin_manager.register(crossover_strategy)
        logger.info("✅ Crossover strategy initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Crossover strategy: {e}")
    
    try:
        from app.strategies.macd import MACDStrategy
        macd_strategy = MACDStrategy(
            fast_period=12,
            slow_period=26,
            signal_period=9,
        )
        await macd_strategy.initialize()
        plugin_manager.register(macd_strategy)
        logger.info("✅ MACD strategy initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MACD strategy: {e}")
    
    # Load notifier plugins
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        try:
            from app.notifications.telegram import TelegramNotifier
            notifier = TelegramNotifier(
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                chat_id=settings.TELEGRAM_CHAT_ID,
            )
            await notifier.initialize()
            plugin_manager.register(notifier)
            logger.info("✅ Telegram notifier initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram notifier: {e}")
    else:
        logger.info("⚠️  Telegram not configured (bot token or chat ID not set)")
    
    # Store in app state
    app_state.plugin_manager = plugin_manager
    
    # Set primary exchange and notifier
    if plugin_manager.exchange_plugins:
        app_state.exchange = list(plugin_manager.exchange_plugins.values())[0]
    
    if plugin_manager.notifier_plugins:
        app_state.notifier = list(plugin_manager.notifier_plugins.values())[0]
    
    # Log summary
    if exchanges_loaded == 0:
        logger.warning("⚠️  No exchanges configured - trading will be disabled")
        logger.info("📖 Add API keys to .env file or use Settings page")
    else:
        logger.info(f"✅ {exchanges_loaded} exchange(s) configured")
    
    logger.info(f"✅ Initialized {len(plugin_manager.all_plugins)} plugins")


async def initialize_services() -> None:
    """Initialize core services."""
    logger.info("Initializing services...")

    if app_state.exchange:
        # Initialize Data Service
        from app.services.data_service import DataService
        app_state.data_service = DataService(app_state.exchange)
        logger.info("Data Service initialized")

        # Initialize Data Collection Manager (for market data)
        from app.services.data_collection_manager import DataCollectionManager
        app_state.data_collection_manager = DataCollectionManager(
            exchange=app_state.exchange,
            db_session=app_state.db_session,
            exchange_name=app_state.exchange.name,
        )
        await app_state.data_collection_manager.start()
        logger.info("✅ Data Collection Manager initialized")

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

    # Stop data collection manager
    if app_state.data_collection_manager:
        await app_state.data_collection_manager.stop()
        logger.info("Data Collection Manager stopped")

    if app_state.plugin_manager:
        await app_state.plugin_manager.shutdown_all()

    logger.info("Cleanup complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global _startup_time

    # Startup
    logger.info("🚀 Crypto Trader starting up...")
    _startup_time = datetime.utcnow()
    app_state.start_time = _startup_time

    # Create default .env if not exists
    create_default_env()

    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")

        # Create database session
        from app.database import AsyncSessionLocal
        app_state.db_session = AsyncSessionLocal()
        logger.info("Database session created")

        # Initialize plugins
        await initialize_plugins()

        # Initialize services
        await initialize_services()

        # Publish system started event
        await publish(
            EventType.SYSTEM_STARTED,
            {"version": "0.2.0"},
            source="main",
        )

        logger.info("✅ Crypto Trader ready!")
        logger.info("📖 Open http://localhost:8000/docs for API documentation")

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

    # Close database session
    if app_state.db_session:
        await app_state.db_session.close()
        logger.info("Database session closed")


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
    from app.api.server import router as server_router
    from app.api.market_data import router as market_data_router
    from app.websocket.routes import router as websocket_router

    app.include_router(health_router)
    app.include_router(config_router)
    app.include_router(orders_router)
    app.include_router(positions_router)
    app.include_router(strategies_router)
    app.include_router(server_router)
    app.include_router(market_data_router)
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
        reload=False,  # Отключаем reload для корректного перезапуска
        workers=1,     # Один worker для корректного выхода
        log_level=settings.APP_LOG_LEVEL.lower(),
    )
