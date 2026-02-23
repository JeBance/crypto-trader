"""Ticker Collector - Background service for collecting 24h ticker statistics."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.types import Ticker as TickerType
from app.plugins.base import ExchangePlugin
from app.models.market_data import Ticker, MonitoredPair
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class TickerCollector:
    """
    Background service for collecting and storing 24h ticker statistics.
    
    Features:
    - Periodic collection for monitored pairs
    - Stores snapshots every N seconds
    - Collection logging and monitoring
    - Graceful shutdown
    
    Usage:
        >>> collector = TickerCollector(exchange, db_session, "binance")
        >>> await collector.start()
        >>> await collector.add_symbol("BTCUSDT")
        >>> # Collector runs in background
        >>> await collector.stop()
    """
    
    def __init__(
        self,
        exchange: ExchangePlugin,
        db_session,  # AsyncSession
        exchange_name: str = "binance",
        collection_interval: int = 60,  # Seconds between collections
        max_concurrent_tasks: int = 10,
    ):
        self.exchange = exchange
        self.db_session = db_session
        self.exchange_name = exchange_name
        self.collection_interval = collection_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # State
        self._running = False
        self._collector_task: Optional[asyncio.Task] = None
        self._monitored_symbols: Dict[str, dict] = {}  # symbol -> config
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Statistics
        self._stats = {
            "collections": 0,
            "tickers_collected": 0,
            "errors": 0,
            "last_collection": None,
        }
    
    async def start(self) -> None:
        """Start the ticker collector."""
        if self._running:
            logger.warning("TickerCollector is already running")
            return
        
        logger.info("Starting TickerCollector...")
        self._running = True
        
        # Load monitored symbols from database
        await self._load_monitored_symbols()
        
        # Start collector loop
        self._collector_task = asyncio.create_task(self._collection_loop())
        
        logger.info(f"TickerCollector started (interval={self.collection_interval}s)")
    
    async def stop(self) -> None:
        """Stop the ticker collector."""
        if not self._running:
            return
        
        logger.info("Stopping TickerCollector...")
        self._running = False
        
        # Cancel collector task
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        
        logger.info("TickerCollector stopped")
    
    async def add_symbol(self, symbol: str) -> None:
        """
        Add a symbol to monitored list.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
        """
        # Update in-memory state
        self._monitored_symbols[symbol] = {
            "is_active": True,
            "last_collection": None,
        }
        
        logger.info(f"Added ticker symbol: {self.exchange_name}:{symbol}")
    
    async def remove_symbol(self, symbol: str) -> None:
        """
        Remove a symbol from monitored list.
        
        NOTE: This does NOT delete historical data!
        """
        self._monitored_symbols.pop(symbol, None)
        logger.info(f"Removed ticker symbol: {self.exchange_name}:{symbol} (data preserved)")
    
    async def _load_monitored_symbols(self) -> None:
        """Load monitored symbols from database."""
        try:
            from sqlalchemy import select, and_
            
            result = await self.db_session.execute(
                select(MonitoredPair).where(
                    and_(
                        MonitoredPair.exchange == self.exchange_name,
                        MonitoredPair.is_active == 1,
                    )
                )
            )
            
            pairs = result.scalars().all()
            
            for pair in pairs:
                self._monitored_symbols[pair.symbol] = {
                    "is_active": True,
                    "last_collection": None,
                }
            
            logger.info(f"Loaded {len(self._monitored_symbols)} monitored symbols from database")
        except Exception as e:
            logger.error(f"Error loading monitored symbols: {e}")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                # Get active symbols
                active_symbols = [
                    symbol
                    for symbol, config in self._monitored_symbols.items()
                    if config["is_active"]
                ]
                
                if not active_symbols:
                    await asyncio.sleep(self.collection_interval)
                    continue
                
                # Collect data for all active symbols
                tasks = [
                    self._collect_ticker(symbol)
                    for symbol in active_symbols
                ]
                
                # Execute with concurrency limit
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update stats
                self._stats["collections"] += 1
                self._stats["last_collection"] = datetime.now(timezone.utc)
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
            
            except asyncio.CancelledError:
                logger.info("TickerCollector loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                self._stats["errors"] += 1
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_ticker(self, symbol: str) -> None:
        """
        Collect ticker data for a single symbol.
        
        Uses semaphore to limit concurrent requests.
        """
        async with self._semaphore:
            if not self._running:
                return
            
            try:
                # Get ticker from exchange
                ticker = await self.exchange.get_ticker(symbol)
                
                if not ticker:
                    logger.warning(f"No ticker received for {symbol}")
                    return
                
                # Save to database
                await self._save_ticker(ticker)
                
                # Update stats
                self._stats["tickers_collected"] += 1
                
                # Update last collection time
                if symbol in self._monitored_symbols:
                    self._monitored_symbols[symbol]["last_collection"] = datetime.now(timezone.utc)
                
                # Log success
                await self._log_collection(
                    symbol=symbol,
                    data_type="ticker",
                    status="success",
                    records_collected=1,
                )
            
            except Exception as e:
                logger.error(f"Error collecting ticker for {symbol}: {e}")
                self._stats["errors"] += 1
                
                # Log error
                await self._log_collection(
                    symbol=symbol,
                    data_type="ticker",
                    status="error",
                    error_message=str(e),
                )
    
    async def _save_ticker(self, ticker: TickerType) -> None:
        """Save ticker to database."""
        try:
            from sqlalchemy import inspect
            
            # Check if session is still valid
            if not inspect(self.db_session).is_active:
                logger.warning("Database session is not active, skipping ticker save")
                return
            
            model = Ticker(
                exchange=self.exchange_name,
                symbol=ticker.symbol,
                timestamp=datetime.now(timezone.utc),
                last_price=ticker.last_price,
                bid_price=ticker.bid,
                ask_price=ticker.ask,
                high_24h=ticker.high_24h,
                low_24h=ticker.low_24h,
                volume_24h=ticker.volume_24h,
                quote_volume_24h=getattr(ticker, 'quote_volume_24h', 0.0),
                change_24h=ticker.change_24h,
                change_percent_24h=ticker.change_percent_24h,
                trades_count_24h=getattr(ticker, 'trades_count_24h', 0),
            )
            
            self.db_session.add(model)
            await self.db_session.commit()
            
            logger.debug(f"Saved ticker for {self.exchange_name}:{ticker.symbol} @ {ticker.last_price}")
        
        except Exception as e:
            logger.error(f"Error saving ticker: {e}")
            try:
                await self.db_session.rollback()
            except:
                pass
    
    async def _log_collection(
        self,
        symbol: str,
        data_type: str,
        status: str,
        records_collected: int = 0,
        error_message: str = None,
    ) -> None:
        """Log collection activity."""
        try:
            from app.models.market_data import DataCollectionLog
            
            log = DataCollectionLog(
                exchange=self.exchange_name,
                symbol=symbol,
                timeframe=None,
                data_type=data_type,
                status=status,
                records_collected=records_collected,
                error_message=error_message,
            )
            
            self.db_session.add(log)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging collection: {e}")
            try:
                await self.db_session.rollback()
            except:
                pass
    
    def get_stats(self) -> dict:
        """Get collector statistics."""
        return {
            "running": self._running,
            "monitored_symbols": len(self._monitored_symbols),
            **self._stats,
        }
    
    def get_monitored_symbols(self) -> Dict[str, dict]:
        """Get list of monitored symbols."""
        return self._monitored_symbols.copy()
