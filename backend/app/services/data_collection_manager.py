"""Data Collection Manager - Orchestrates all data collectors."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.plugins.base import ExchangePlugin
from app.services.candle_collector import CandleCollector
from app.services.ticker_collector import TickerCollector
from app.services.trade_collector import TradeCollector
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class DataCollectionManager:
    """
    Central manager for all data collection activities.
    
    Orchestrates:
    - Candle collection (continuous)
    - Ticker collection (periodic)
    - Trade collection (periodic)
    - Order book collection (optional)
    
    Usage:
        >>> manager = DataCollectionManager(exchange, db_session, "binance")
        >>> await manager.start()
        >>> await manager.add_monitored_pair("BTCUSDT", ["1h", "4h", "1d"])
        >>> stats = manager.get_stats()
        >>> await manager.stop()
    """
    
    def __init__(
        self,
        exchange: ExchangePlugin,
        db_session: AsyncSession,
        exchange_name: str = "binance",
        candle_collection_interval: int = 10,
        ticker_collection_interval: int = 60,
        trade_collection_interval: int = 30,
    ):
        self.exchange = exchange
        self.db_session = db_session
        self.exchange_name = exchange_name
        
        # Initialize collectors
        self.candle_collector = CandleCollector(
            exchange=exchange,
            db_session=db_session,
            exchange_name=exchange_name,
            collection_interval=candle_collection_interval,
        )
        
        self.ticker_collector = TickerCollector(
            exchange=exchange,
            db_session=db_session,
            exchange_name=exchange_name,
            collection_interval=ticker_collection_interval,
        )
        
        self.trade_collector = TradeCollector(
            exchange=exchange,
            db_session=db_session,
            exchange_name=exchange_name,
            collection_interval=trade_collection_interval,
        )
        
        # Market data service (shared)
        self.market_data_service = MarketDataService(
            exchange=exchange,
            db_session=db_session,
            exchange_name=exchange_name,
        )
        
        # State
        self._running = False
        self._monitored_pairs: Dict[str, dict] = {}
        
        logger.info(f"DataCollectionManager initialized for {exchange_name}")
    
    async def start(self) -> None:
        """Start all collectors."""
        if self._running:
            logger.warning("DataCollectionManager is already running")
            return
        
        logger.info("Starting DataCollectionManager...")
        self._running = True
        
        # Start all collectors
        await self.candle_collector.start()
        await self.ticker_collector.start()
        await self.trade_collector.start()
        
        logger.info("DataCollectionManager started (candles, tickers, trades)")
    
    async def stop(self) -> None:
        """Stop all collectors."""
        if not self._running:
            return
        
        logger.info("Stopping DataCollectionManager...")
        self._running = False
        
        # Stop all collectors
        await self.candle_collector.stop()
        await self.ticker_collector.stop()
        await self.trade_collector.stop()
        
        logger.info("DataCollectionManager stopped")
    
    async def add_monitored_pair(
        self,
        symbol: str,
        timeframes: List[str],
        is_active: bool = True,
    ) -> None:
        """
        Add a trading pair to monitored list.
        
        Args:
            symbol: Trading pair symbol
            timeframes: List of timeframes to collect
            is_active: Whether to actively collect data
        """
        await self.candle_collector.add_monitored_pair(symbol, timeframes, is_active)
        await self.ticker_collector.add_symbol(symbol)
        await self.trade_collector.add_symbol(symbol)
        
        self._monitored_pairs[symbol] = {
            "timeframes": timeframes,
            "is_active": is_active,
        }
        
        logger.info(f"Added monitored pair: {self.exchange_name}:{symbol}")
    
    async def remove_monitored_pair(self, symbol: str) -> None:
        """
        Remove a pair from monitored list.
        
        NOTE: Historical data is preserved!
        """
        await self.candle_collector.remove_monitored_pair(symbol)
        await self.ticker_collector.remove_symbol(symbol)
        await self.trade_collector.remove_symbol(symbol)
        
        self._monitored_pairs.pop(symbol, None)
        
        logger.info(f"Removed monitored pair: {self.exchange_name}:{symbol} (data preserved)")
    
    async def resume_monitored_pair(self, symbol: str) -> None:
        """
        Resume monitoring for a previously monitored pair.
        
        Will automatically backfill missing data.
        """
        await self.candle_collector.resume_monitored_pair(symbol)
        await self.ticker_collector.add_symbol(symbol)
        await self.trade_collector.add_symbol(symbol)
        
        logger.info(f"Resumed monitoring for: {self.exchange_name}:{symbol}")
    
    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ):
        """
        Get historical candles (from DB or exchange).
        
        Smart loading:
        1. Try to load from database
        2. If not enough data, fetch from exchange
        3. Save to database
        4. Return combined data
        """
        return await self.market_data_service.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            use_db=True,
        )
    
    async def get_ticker(self, symbol: str):
        """Get latest ticker data."""
        return await self.market_data_service.get_ticker(symbol)
    
    async def backfill_historical_data(
        self,
        symbol: str,
        timeframes: List[str],
        days: int = 30,
    ) -> None:
        """
        Backfill historical data for a pair.
        
        Args:
            symbol: Trading pair symbol
            timeframes: Timeframes to backfill
            days: Number of days to backfill
        """
        await self.candle_collector._backfill_missing_data(symbol, timeframes, days)
        
        logger.info(f"Backfill completed for {symbol}")
    
    def get_stats(self) -> dict:
        """Get collection statistics."""
        candle_stats = self.candle_collector.get_stats()
        ticker_stats = self.ticker_collector.get_stats()
        trade_stats = self.trade_collector.get_stats()
        
        return {
            "exchange": self.exchange_name,
            "running": self._running,
            "monitored_pairs": len(self._monitored_pairs),
            "candle_collector": candle_stats,
            "ticker_collector": ticker_stats,
            "trade_collector": trade_stats,
        }
    
    def get_monitored_pairs(self) -> Dict[str, dict]:
        """Get list of monitored pairs."""
        return self._monitored_pairs.copy()
    
    @property
    def is_running(self) -> bool:
        """Check if manager is running."""
        return self._running
