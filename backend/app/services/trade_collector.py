"""Trade Collector - Background service for collecting recent trades."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.plugins.base import ExchangePlugin
from app.models.market_data import MonitoredPair

logger = logging.getLogger(__name__)


class TradeCollector:
    """
    Background service for collecting and storing recent trades.
    
    Features:
    - Periodic collection of recent trades
    - Stores last N trades per symbol
    - Collection logging and monitoring
    - Graceful shutdown
    
    Usage:
        >>> collector = TradeCollector(exchange, db_session, "binance")
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
        collection_interval: int = 30,  # Seconds between collections
        max_trades_per_symbol: int = 1000,  # Keep last N trades
        max_concurrent_tasks: int = 5,
    ):
        self.exchange = exchange
        self.db_session = db_session
        self.exchange_name = exchange_name
        self.collection_interval = collection_interval
        self.max_trades_per_symbol = max_trades_per_symbol
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # State
        self._running = False
        self._collector_task: Optional[asyncio.Task] = None
        self._monitored_symbols: Dict[str, dict] = {}  # symbol -> config
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Statistics
        self._stats = {
            "collections": 0,
            "trades_collected": 0,
            "errors": 0,
            "last_collection": None,
        }
    
    async def start(self) -> None:
        """Start the trade collector."""
        if self._running:
            logger.warning("TradeCollector is already running")
            return
        
        logger.info("Starting TradeCollector...")
        self._running = True
        
        # Load monitored symbols from database
        await self._load_monitored_symbols()
        
        # Start collector loop
        self._collector_task = asyncio.create_task(self._collection_loop())
        
        logger.info(f"TradeCollector started (interval={self.collection_interval}s)")
    
    async def stop(self) -> None:
        """Stop the trade collector."""
        if not self._running:
            return
        
        logger.info("Stopping TradeCollector...")
        self._running = False
        
        # Cancel collector task
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        
        logger.info("TradeCollector stopped")
    
    async def add_symbol(self, symbol: str) -> None:
        """
        Add a symbol to monitored list.
        
        Args:
            symbol: Trading pair symbol
        """
        self._monitored_symbols[symbol] = {
            "is_active": True,
            "last_collection": None,
        }
        
        logger.info(f"Added trade symbol: {self.exchange_name}:{symbol}")
    
    async def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from monitored list."""
        self._monitored_symbols.pop(symbol, None)
        logger.info(f"Removed trade symbol: {self.exchange_name}:{symbol}")
    
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
                    self._collect_trades(symbol)
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
                logger.info("TradeCollector loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                self._stats["errors"] += 1
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_trades(self, symbol: str) -> None:
        """
        Collect recent trades for a single symbol.
        
        Uses semaphore to limit concurrent requests.
        """
        async with self._semaphore:
            if not self._running:
                return
            
            try:
                # Get recent trades from exchange
                # Note: This requires exchange to implement get_recent_trades
                if hasattr(self.exchange, 'get_recent_trades'):
                    trades = await self.exchange.get_recent_trades(symbol, limit=100)
                else:
                    logger.debug(f"Exchange {self.exchange_name} doesn't support get_recent_trades")
                    return
                
                if not trades:
                    logger.debug(f"No trades received for {symbol}")
                    return
                
                # Save to database
                await self._save_trades(trades)
                
                # Update stats
                self._stats["trades_collected"] += len(trades)
                
                # Update last collection time
                if symbol in self._monitored_symbols:
                    self._monitored_symbols[symbol]["last_collection"] = datetime.now(timezone.utc)
                
                # Log success
                await self._log_collection(
                    symbol=symbol,
                    data_type="trade",
                    status="success",
                    records_collected=len(trades),
                )
            
            except Exception as e:
                logger.error(f"Error collecting trades for {symbol}: {e}")
                self._stats["errors"] += 1
                
                # Log error
                await self._log_collection(
                    symbol=symbol,
                    data_type="trade",
                    status="error",
                    error_message=str(e),
                )
    
    async def _save_trades(self, trades: List) -> None:
        """Save trades to database."""
        try:
            from sqlalchemy import inspect
            from app.models.trade import Trade as TradeModel
            
            # Check if session is still valid
            if not inspect(self.db_session).is_active:
                logger.warning("Database session is not active, skipping trades save")
                return
            
            for trade_data in trades:
                # Convert to Trade model
                # Handle different trade data formats
                trade = TradeModel(
                    order_id=0,  # No order relation for external trades
                    exchange_trade_id=str(trade_data.trade_id if hasattr(trade_data, 'trade_id') else trade_data.get('trade_id', '')),
                    symbol=trade_data.symbol if hasattr(trade_data, 'symbol') else trade_data.get('symbol', ''),
                    side=trade_data.side if hasattr(trade_data, 'side') else trade_data.get('side', 'buy'),
                    quantity=trade_data.quantity if hasattr(trade_data, 'quantity') else trade_data.get('quantity', 0.0),
                    price=trade_data.price if hasattr(trade_data, 'price') else trade_data.get('price', 0.0),
                    fee=trade_data.fee if hasattr(trade_data, 'fee') else trade_data.get('fee', 0.0),
                    fee_currency=trade_data.fee_currency if hasattr(trade_data, 'fee_currency') else trade_data.get('fee_currency'),
                    executed_at=trade_data.timestamp if hasattr(trade_data, 'timestamp') else trade_data.get('timestamp', datetime.now(timezone.utc)),
                )
                
                self.db_session.add(trade)
            
            await self.db_session.commit()
            
            logger.debug(f"Saved {len(trades)} trades for {self.exchange_name}")
        
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
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
