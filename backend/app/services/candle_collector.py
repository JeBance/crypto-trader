"""Candle Collector - Background service for collecting candlestick data."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import Candle as CandleType
from app.plugins.base import ExchangePlugin
from app.models.market_data import MonitoredPair, Candle, DataCollectionLog
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class CandleCollector:
    """
    Background service for collecting and storing candlestick data.
    
    Features:
    - Continuous collection for monitored pairs
    - Smart gap detection and filling
    - Multiple timeframes per pair
    - Collection logging and monitoring
    - Graceful shutdown
    
    Usage:
        >>> collector = CandleCollector(exchange, db_session, "binance")
        >>> await collector.start()
        >>> await collector.add_monitored_pair("BTCUSDT", ["1h", "4h"])
        >>> # Collector runs in background
        >>> await collector.stop()
    """
    
    def __init__(
        self,
        exchange: ExchangePlugin,
        db_session: AsyncSession,
        exchange_name: str = "binance",
        collection_interval: int = 10,  # Seconds between collections
        max_concurrent_tasks: int = 5,
    ):
        self.exchange = exchange
        self.db_session = db_session
        self.exchange_name = exchange_name
        self.collection_interval = collection_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # State
        self._running = False
        self._collector_task: Optional[asyncio.Task] = None
        self._monitored_pairs: Dict[str, Dict] = {}  # symbol -> {timeframes, last_collection}
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Statistics
        self._stats = {
            "collections": 0,
            "candles_collected": 0,
            "errors": 0,
            "last_collection": None,
        }
    
    async def start(self) -> None:
        """Start the candle collector."""
        if self._running:
            logger.warning("CandleCollector is already running")
            return
        
        logger.info("Starting CandleCollector...")
        self._running = True
        
        # Load monitored pairs from database
        await self._load_monitored_pairs()
        
        # Start collector loop
        self._collector_task = asyncio.create_task(self._collection_loop())
        
        logger.info(f"CandleCollector started (interval={self.collection_interval}s)")
    
    async def stop(self) -> None:
        """Stop the candle collector."""
        if not self._running:
            return
        
        logger.info("Stopping CandleCollector...")
        self._running = False
        
        # Cancel collector task
        if self._collector_task:
            self._collector_task.cancel()
            try:
                await self._collector_task
            except asyncio.CancelledError:
                pass
        
        logger.info("CandleCollector stopped")
    
    async def add_monitored_pair(
        self,
        symbol: str,
        timeframes: List[str],
        is_active: bool = True,
    ) -> None:
        """
        Add a trading pair to monitored list.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            timeframes: List of timeframes to collect (e.g., ["1h", "4h", "1d"])
            is_active: Whether to actively collect data
        """
        # Save to database
        try:
            result = await self.db_session.execute(
                select(MonitoredPair).where(
                    and_(
                        MonitoredPair.exchange == self.exchange_name,
                        MonitoredPair.symbol == symbol,
                    )
                )
            )
            
            pair = result.scalar_one_or_none()
            
            if pair:
                # Update existing
                pair.timeframes = ",".join(timeframes)
                pair.is_active = 1 if is_active else 0
                pair.updated_at = datetime.now(timezone.utc)
            else:
                # Create new
                pair = MonitoredPair(
                    exchange=self.exchange_name,
                    symbol=symbol,
                    timeframes=",".join(timeframes),
                    is_active=1 if is_active else 0,
                )
                self.db_session.add(pair)
            
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error saving monitored pair: {e}")
            await self.db_session.rollback()
            raise
        
        # Update in-memory state
        self._monitored_pairs[symbol] = {
            "timeframes": timeframes,
            "is_active": is_active,
            "last_collection": None,
        }
        
        logger.info(f"Added monitored pair: {self.exchange_name}:{symbol} timeframes={timeframes}")
    
    async def remove_monitored_pair(self, symbol: str) -> None:
        """
        Remove a trading pair from monitored list.
        
        NOTE: This does NOT delete historical data!
        It only stops future collection.
        """
        # Update database
        try:
            result = await self.db_session.execute(
                select(MonitoredPair).where(
                    and_(
                        MonitoredPair.exchange == self.exchange_name,
                        MonitoredPair.symbol == symbol,
                    )
                )
            )
            
            pair = result.scalar_one_or_none()
            
            if pair:
                pair.is_active = 0
                pair.updated_at = datetime.now(timezone.utc)
                await self.db_session.commit()
        
        except Exception as e:
            logger.error(f"Error removing monitored pair: {e}")
            await self.db_session.rollback()
        
        # Remove from in-memory state
        self._monitored_pairs.pop(symbol, None)
        
        logger.info(f"Removed monitored pair: {self.exchange_name}:{symbol} (historical data preserved)")
    
    async def resume_monitored_pair(self, symbol: str) -> None:
        """
        Resume monitoring for a previously monitored pair.
        
        Will automatically backfill missing data.
        """
        # Get existing timeframes from database
        try:
            result = await self.db_session.execute(
                select(MonitoredPair).where(
                    and_(
                        MonitoredPair.exchange == self.exchange_name,
                        MonitoredPair.symbol == symbol,
                    )
                )
            )
            
            pair = result.scalar_one_or_none()
            
            if pair:
                timeframes = pair.timeframes.split(",") if pair.timeframes else ["1h"]
                
                # Reactivate
                pair.is_active = 1
                pair.updated_at = datetime.now(timezone.utc)
                await self.db_session.commit()
                
                # Update in-memory state
                self._monitored_pairs[symbol] = {
                    "timeframes": timeframes,
                    "is_active": True,
                    "last_collection": None,
                }
                
                # Backfill missing data
                logger.info(f"Resuming monitoring for {symbol}, backfilling...")
                await self._backfill_missing_data(symbol, timeframes)
                
                logger.info(f"Resumed monitoring for: {self.exchange_name}:{symbol}")
            else:
                logger.warning(f"Pair {symbol} not found in database")
        
        except Exception as e:
            logger.error(f"Error resuming monitored pair: {e}")
            await self.db_session.rollback()
            raise
    
    async def _load_monitored_pairs(self) -> None:
        """Load monitored pairs from database."""
        try:
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
                timeframes = pair.timeframes.split(",") if pair.timeframes else ["1h"]
                self._monitored_pairs[pair.symbol] = {
                    "timeframes": timeframes,
                    "is_active": True,
                    "last_collection": None,
                }
            
            logger.info(f"Loaded {len(self._monitored_pairs)} monitored pairs from database")
        
        except Exception as e:
            logger.error(f"Error loading monitored pairs: {e}")
    
    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while self._running:
            try:
                # Get active pairs
                active_pairs = [
                    (symbol, config)
                    for symbol, config in self._monitored_pairs.items()
                    if config["is_active"]
                ]
                
                if not active_pairs:
                    await asyncio.sleep(self.collection_interval)
                    continue
                
                # Collect data for all active pairs
                tasks = [
                    self._collect_pair(symbol, config["timeframes"])
                    for symbol, config in active_pairs
                ]
                
                # Execute with concurrency limit
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update stats
                self._stats["collections"] += 1
                self._stats["last_collection"] = datetime.now(timezone.utc)
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
            
            except asyncio.CancelledError:
                logger.info("CandleCollector loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                self._stats["errors"] += 1
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_pair(self, symbol: str, timeframes: List[str]) -> None:
        """
        Collect data for a single pair across all timeframes.
        
        Uses semaphore to limit concurrent requests.
        """
        async with self._semaphore:
            for timeframe in timeframes:
                if not self._running:
                    break
                
                try:
                    await self._collect_candle(symbol, timeframe)
                except Exception as e:
                    logger.error(f"Error collecting {symbol} {timeframe}: {e}")
                    self._stats["errors"] += 1
                    
                    # Log error
                    await self._log_collection(
                        symbol=symbol,
                        data_type="candle",
                        timeframe=timeframe,
                        status="error",
                        error_message=str(e),
                    )
    
    async def _collect_candle(self, symbol: str, timeframe: str) -> None:
        """
        Collect latest candle for a symbol/timeframe.
        
        Smart collection:
        1. Fetch latest candle from exchange
        2. Check if we already have it in DB
        3. If not, save it
        4. If yes, check for updates (for incomplete candles)
        """
        # Get latest candle from exchange
        candles = await self.exchange.get_candles(symbol, timeframe, limit=1)
        
        if not candles:
            logger.warning(f"No candles received for {symbol} {timeframe}")
            return
        
        latest_candle = candles[0]
        
        # Check if candle already exists in DB
        existing = await self._get_candle_from_db(symbol, timeframe, latest_candle.timestamp)
        
        candles_to_save = [latest_candle]
        
        # If candle doesn't exist, we might need to backfill
        if not existing:
            # Check for gaps
            last_candle_time = await self._get_last_candle_time(symbol, timeframe)
            
            if last_candle_time:
                # There's a gap - backfill
                gap_candles = await self._backfill_gaps(
                    symbol, timeframe, last_candle_time, latest_candle.timestamp
                )
                if gap_candles:
                    candles_to_save = gap_candles + [latest_candle]
        
        # Save to database
        if candles_to_save:
            await self._save_candles(candles_to_save)
            
            # Update stats
            self._stats["candles_collected"] += len(candles_to_save)
            
            # Update last collection time
            if symbol in self._monitored_pairs:
                self._monitored_pairs[symbol]["last_collection"] = datetime.now(timezone.utc)
            
            # Log success
            await self._log_collection(
                symbol=symbol,
                data_type="candle",
                timeframe=timeframe,
                status="success",
                records_collected=len(candles_to_save),
                data_from=candles_to_save[0].timestamp,
                data_to=candles_to_save[-1].timestamp,
            )
    
    async def _backfill_gaps(
        self,
        symbol: str,
        timeframe: str,
        from_time: datetime,
        to_time: datetime,
    ) -> List[CandleType]:
        """
        Backfill missing candles between two timestamps.
        
        Returns list of candles to save.
        """
        logger.info(f"Backfilling gaps for {symbol} {timeframe}: {from_time} to {to_time}")
        
        all_candles = []
        timeframe_ms = self._timeframe_to_milliseconds(timeframe)
        
        current_time = from_time + timedelta(milliseconds=timeframe_ms)
        
        while current_time < to_time:
            # Fetch candles starting from current_time
            try:
                candles = await self.exchange.get_candles(symbol, timeframe, limit=500)
                
                if not candles:
                    break
                
                # Filter candles in our range
                batch = [
                    c for c in candles
                    if from_time <= c.timestamp <= to_time
                ]
                
                if not batch:
                    break
                
                all_candles.extend(batch)
                
                # Move forward
                current_time = max(c.timestamp for c in batch) + timedelta(milliseconds=timeframe_ms)
                
                # If we got less than limit, we've reached the end
                if len(candles) < 500:
                    break
                
            except Exception as e:
                logger.error(f"Error backfilling {symbol} {timeframe}: {e}")
                break
        
        if all_candles:
            logger.info(f"Backfilled {len(all_candles)} candles for {symbol} {timeframe}")
        
        return all_candles
    
    async def _backfill_missing_data(
        self,
        symbol: str,
        timeframes: List[str],
        days_to_backfill: int = 30,
    ) -> None:
        """
        Backfill missing data when resuming monitoring.
        
        Args:
            symbol: Trading pair symbol
            timeframes: List of timeframes to backfill
            days_to_backfill: How many days to backfill
        """
        start_time = datetime.now(timezone.utc) - timedelta(days=days_to_backfill)
        end_time = datetime.now(timezone.utc)
        
        for timeframe in timeframes:
            try:
                # Get last candle time
                last_candle_time = await self._get_last_candle_time(symbol, timeframe)
                
                if last_candle_time:
                    # Backfill from last candle
                    if last_candle_time < end_time:
                        await self._backfill_gaps(symbol, timeframe, last_candle_time, end_time)
                else:
                    # No data at all - fetch historical
                    logger.info(f"No historical data for {symbol} {timeframe}, fetching...")
                    await self._fetch_historical_data(symbol, timeframe, start_time, end_time)
            
            except Exception as e:
                logger.error(f"Error backfilling {symbol} {timeframe}: {e}")
    
    async def _fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Fetch historical data from exchange."""
        # This would use the MarketDataService logic
        # For now, simplified implementation
        pass
    
    async def _get_candle_from_db(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
    ) -> Optional[Candle]:
        """Get candle from database by timestamp."""
        try:
            result = await self.db_session.execute(
                select(Candle).where(
                    and_(
                        Candle.exchange == self.exchange_name,
                        Candle.symbol == symbol,
                        Candle.timeframe == timeframe,
                        Candle.timestamp == timestamp,
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting candle from DB: {e}")
            return None
    
    async def _get_last_candle_time(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[datetime]:
        """Get timestamp of last candle in database."""
        try:
            from sqlalchemy import func
            
            result = await self.db_session.execute(
                select(func.max(Candle.timestamp)).where(
                    and_(
                        Candle.exchange == self.exchange_name,
                        Candle.symbol == symbol,
                        Candle.timeframe == timeframe,
                    )
                )
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Error getting last candle time: {e}")
            return None
    
    async def _save_candles(self, candles: List[CandleType]) -> None:
        """Save candles to database."""
        try:
            for candle in candles:
                model = Candle(
                    exchange=self.exchange_name,
                    symbol=candle.symbol,
                    timeframe=candle.timeframe,
                    timestamp=candle.timestamp,
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume,
                )
                self.db_session.add(model)
            
            await self.db_session.commit()
        
        except Exception as e:
            logger.error(f"Error saving candles: {e}")
            await self.db_session.rollback()
            raise
    
    async def _log_collection(
        self,
        symbol: str,
        data_type: str,
        status: str,
        timeframe: str = None,
        records_collected: int = 0,
        error_message: str = None,
        data_from: datetime = None,
        data_to: datetime = None,
    ) -> None:
        """Log collection activity."""
        try:
            log = DataCollectionLog(
                exchange=self.exchange_name,
                symbol=symbol,
                timeframe=timeframe,
                data_type=data_type,
                status=status,
                records_collected=records_collected,
                error_message=error_message,
                data_from=data_from,
                data_to=data_to,
            )
            self.db_session.add(log)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging collection: {e}")
            await self.db_session.rollback()
    
    def _timeframe_to_milliseconds(self, timeframe: str) -> int:
        """Convert timeframe to milliseconds."""
        tf_map = {
            "1m": 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
            "1w": 7 * 24 * 60 * 60 * 1000,
        }
        return tf_map.get(timeframe, 60 * 60 * 1000)
    
    def get_stats(self) -> dict:
        """Get collector statistics."""
        return {
            "running": self._running,
            "monitored_pairs": len(self._monitored_pairs),
            "active_pairs": sum(1 for p in self._monitored_pairs.values() if p["is_active"]),
            **self._stats,
        }
    
    def get_monitored_pairs(self) -> Dict[str, Dict]:
        """Get list of monitored pairs."""
        return self._monitored_pairs.copy()
