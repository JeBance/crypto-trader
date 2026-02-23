"""Enhanced Data Service with database persistence and smart loading."""

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import Candle as CandleType, Ticker as TickerType, Trade as TradeType
from app.plugins.base import ExchangePlugin
from app.models.market_data import (
    Ticker as TickerModel,
    Trade as TradeModel,
    MonitoredPair,
    DataCollectionLog,
)
from app.models.candle import Candle as CandleModel

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache.
    
    Example:
        >>> cache = LRUCache(max_size=100)
        >>> cache.set("key", "value")
        >>> value = cache.get("key")
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
    
    def get(self, key: str, default=None):
        """Get value from cache."""
        if key not in self._cache:
            return default
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value) -> None:
        """Set value in cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        
        # Remove oldest if over capacity
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache


class MarketDataService:
    """
    Enhanced service for retrieving, caching, and persisting market data.
    
    Features:
    - Automatic saving to database
    - Smart loading from database with gap detection
    - LRU caching for performance
    - Support for multiple exchanges
    - Collection logging and monitoring
    
    Example:
        >>> service = MarketDataService(exchange, db_session)
        >>> candles = await service.get_candles("BTCUSDT", "1h", limit=100)
        >>> await service.save_ticker(ticker)
    """
    
    def __init__(
        self,
        exchange: ExchangePlugin,
        db_session: AsyncSession,
        exchange_name: str = "binance",
        cache_size: int = 1000,
    ):
        self.exchange = exchange
        self.db_session = db_session
        self.exchange_name = exchange_name
        
        # Caches
        self._candle_cache: Dict[str, LRUCache] = {}  # symbol_timeframe -> LRUCache
        self._ticker_cache: LRUCache = LRUCache(cache_size)
        self._last_update: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=30)  # Cache TTL for tickers
        
        # Collection state
        self._monitored_pairs: Dict[str, dict] = {}  # symbol -> config
        self._collection_tasks: Dict[str, asyncio.Task] = {}
    
    def _get_candle_cache_key(self, symbol: str, timeframe: str) -> str:
        """Generate cache key for candles."""
        return f"{self.exchange_name}_{symbol}_{timeframe}"
    
    def _get_ticker_cache_key(self, symbol: str) -> str:
        """Generate cache key for ticker."""
        return f"{self.exchange_name}_{symbol}"
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        use_cache: bool = True,
        use_db: bool = True,
    ) -> List[CandleType]:
        """
        Get candlestick data with smart loading from DB.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            limit: Number of candles to retrieve
            use_cache: Whether to use cache
            use_db: Whether to use database
            
        Returns:
            List of candles
        """
        cache_key = self._get_candle_cache_key(symbol, timeframe)
        
        # Check cache first
        if use_cache and cache_key in self._candle_cache:
            cached = self._candle_cache[cache_key].get("candles")
            if cached:
                logger.debug(f"Cache hit for {self.exchange_name}:{symbol} {timeframe}")
                return cached
        
        # Try to load from database
        if use_db:
            db_candles = await self._load_candles_from_db(symbol, timeframe, limit)
            if db_candles:
                logger.debug(f"DB hit for {self.exchange_name}:{symbol} {timeframe} ({len(db_candles)} candles)")
                
                # Update cache
                self._update_candle_cache(cache_key, db_candles)
                return db_candles
        
        # Fetch from exchange
        logger.debug(f"Fetching candles from exchange for {self.exchange_name}:{symbol} {timeframe}")
        candles = await self.exchange.get_candles(symbol, timeframe, limit)
        
        if candles:
            # Save to database
            await self._save_candles_to_db(candles)
            
            # Update cache
            self._update_candle_cache(cache_key, candles)
        
        return candles
    
    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime = None,
    ) -> List[CandleType]:
        """
        Get historical candles between two dates with smart gap filling.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            start_time: Start datetime
            end_time: End datetime (default: now)
            
        Returns:
            List of historical candles
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        
        logger.info(f"Loading historical data for {self.exchange_name}:{symbol} {timeframe}")
        logger.info(f"Date range: {start_time} to {end_time}")
        
        # Step 1: Load from database
        db_candles = await self._load_candles_from_db_by_range(
            symbol, timeframe, start_time, end_time
        )
        
        if not db_candles:
            logger.info(f"No data in DB, fetching from exchange...")
            return await self._fetch_historical_data(symbol, timeframe, start_time, end_time)
        
        # Step 2: Check for gaps
        gaps = await self._detect_gaps(symbol, timeframe, start_time, end_time, db_candles)
        
        if gaps:
            logger.info(f"Found {len(gaps)} gaps in historical data")
            # Step 3: Fill gaps from exchange
            for gap_from, gap_to in gaps:
                logger.info(f"Filling gap: {gap_from} to {gap_to}")
                gap_candles = await self._fetch_historical_data(symbol, timeframe, gap_from, gap_to)
                if gap_candles:
                    await self._save_candles_to_db(gap_candles)
                    db_candles.extend(gap_candles)
        
        # Sort by timestamp
        db_candles.sort(key=lambda c: c.timestamp)
        
        # Update cache
        cache_key = self._get_candle_cache_key(symbol, timeframe)
        self._update_candle_cache(cache_key, db_candles)
        
        return db_candles
    
    async def _fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[CandleType]:
        """
        Fetch historical data from exchange with pagination.
        
        Binance/Bybit allow up to 1000 candles per request.
        We need to paginate for large date ranges.
        """
        all_candles = []
        timeframe_ms = self._timeframe_to_milliseconds(timeframe)
        
        current_time = start_time
        while current_time < end_time:
            # Fetch batch
            candles = await self.exchange.get_candles(symbol, timeframe, limit=1000)
            
            if not candles:
                break
            
            # Filter by time range
            batch = [c for c in candles if start_time <= c.timestamp <= end_time]
            
            if not batch:
                break
            
            all_candles.extend(batch)
            
            # Move to next batch
            # Find the earliest candle timestamp and move forward
            if batch:
                current_time = min(c.timestamp for c in batch)
                current_time = datetime.fromtimestamp(
                    current_time.timestamp() - (timeframe_ms / 1000),
                    tz=timezone.utc
                )
            else:
                break
            
            # Avoid infinite loop
            if len(batch) < 1000:
                break
        
        # Save to database
        if all_candles:
            await self._save_candles_to_db(all_candles)
            logger.info(f"Saved {len(all_candles)} historical candles")
        
        return all_candles
    
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
        return tf_map.get(timeframe, 60 * 60 * 1000)  # Default 1h
    
    async def _detect_gaps(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        candles: List[CandleType],
    ) -> List[Tuple[datetime, datetime]]:
        """
        Detect gaps in candle data.
        
        Returns list of (gap_start, gap_end) tuples.
        """
        if not candles:
            return [(start_time, end_time)]
        
        gaps = []
        timeframe_ms = self._timeframe_to_milliseconds(timeframe)
        tolerance_ms = timeframe_ms * 0.5  # 50% tolerance
        
        # Sort candles by timestamp
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        
        # Check gap at the beginning
        if sorted_candles[0].timestamp > start_time + timedelta(milliseconds=tolerance_ms):
            gaps.append((start_time, sorted_candles[0].timestamp))
        
        # Check gaps between candles
        for i in range(1, len(sorted_candles)):
            prev_candle = sorted_candles[i - 1]
            curr_candle = sorted_candles[i]
            
            expected_next = datetime.fromtimestamp(
                prev_candle.timestamp.timestamp() + (timeframe_ms / 1000),
                tz=timezone.utc
            )
            
            if curr_candle.timestamp > expected_next + timedelta(milliseconds=tolerance_ms):
                gaps.append((expected_next, curr_candle.timestamp))
        
        # Check gap at the end
        last_candle_time = sorted_candles[-1].timestamp
        if last_candle_time < end_time - timedelta(milliseconds=tolerance_ms):
            gaps.append((last_candle_time, end_time))
        
        return gaps
    
    async def get_ticker(self, symbol: str, use_cache: bool = True) -> Optional[TickerType]:
        """
        Get ticker data.
        
        Args:
            symbol: Trading pair symbol
            use_cache: Whether to use cache
            
        Returns:
            Ticker data or None
        """
        cache_key = self._get_ticker_cache_key(symbol)
        
        # Check cache and TTL
        if use_cache:
            cached = self._ticker_cache.get(cache_key)
            last_update = self._last_update.get(cache_key)
            
            if cached and last_update:
                if datetime.now(timezone.utc) - last_update < self._cache_ttl:
                    logger.debug(f"Cache hit for ticker {self.exchange_name}:{symbol}")
                    return cached
        
        # Fetch from exchange
        logger.debug(f"Fetching ticker for {self.exchange_name}:{symbol}")
        ticker = await self.exchange.get_ticker(symbol)
        
        if ticker:
            # Update cache
            self._ticker_cache.set(cache_key, ticker)
            self._last_update[cache_key] = datetime.now(timezone.utc)
        
        return ticker
    
    async def _load_candles_from_db(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[CandleType]:
        """Load candles from database."""
        try:
            result = await self.db_session.execute(
                select(CandleModel)
                .where(
                    and_(
                        CandleModel.exchange == self.exchange_name,
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                    )
                )
                .order_by(CandleModel.timestamp.desc())
                .limit(limit)
            )
            
            models = result.scalars().all()
            
            # Convert to CandleType
            return [self._model_to_candle(m) for m in reversed(models)]
        
        except Exception as e:
            logger.error(f"Error loading candles from DB: {e}")
            return []
    
    async def _load_candles_from_db_by_range(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[CandleType]:
        """Load candles from database by time range."""
        try:
            result = await self.db_session.execute(
                select(CandleModel)
                .where(
                    and_(
                        CandleModel.exchange == self.exchange_name,
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                        CandleModel.timestamp >= start_time,
                        CandleModel.timestamp <= end_time,
                    )
                )
                .order_by(CandleModel.timestamp.asc())
            )
            
            models = result.scalars().all()
            return [self._model_to_candle(m) for m in models]
        
        except Exception as e:
            logger.error(f"Error loading candles from DB by range: {e}")
            return []
    
    async def _save_candles_to_db(self, candles: List[CandleType]) -> None:
        """Save candles to database with upsert (ignore duplicates)."""
        try:
            for candle in candles:
                model = CandleModel(
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
                
                # Use INSERT OR IGNORE (SQLite) / ON CONFLICT DO NOTHING (PostgreSQL)
                self.db_session.add(model)
            
            await self.db_session.commit()
            logger.debug(f"Saved {len(candles)} candles to DB for {self.exchange_name}:{candles[0].symbol}")
        
        except Exception as e:
            logger.error(f"Error saving candles to DB: {e}")
            await self.db_session.rollback()
    
    async def _save_ticker_to_db(self, ticker: TickerType) -> None:
        """Save ticker snapshot to database."""
        try:
            model = TickerModel(
                exchange=self.exchange_name,
                symbol=ticker.symbol,
                timestamp=datetime.now(timezone.utc),
                last_price=ticker.last_price,
                bid_price=ticker.bid,
                ask_price=ticker.ask,
                high_24h=ticker.high_24h,
                low_24h=ticker.low_24h,
                volume_24h=ticker.volume_24h,
                change_24h=ticker.change_24h,
                change_percent_24h=ticker.change_percent_24h,
            )
            
            self.db_session.add(model)
            await self.db_session.commit()
        
        except Exception as e:
            logger.error(f"Error saving ticker to DB: {e}")
            await self.db_session.rollback()
    
    def _update_candle_cache(self, cache_key: str, candles: List[CandleType]) -> None:
        """Update candle cache."""
        if cache_key not in self._candle_cache:
            self._candle_cache[cache_key] = LRUCache(10)
        
        self._candle_cache[cache_key].set("candles", candles)
        self._candle_cache[cache_key].set("timestamp", datetime.now(timezone.utc))
    
    def _model_to_candle(self, model: CandleModel) -> CandleType:
        """Convert database model to CandleType."""
        return CandleType(
            symbol=model.symbol,
            timeframe=model.timeframe,
            timestamp=model.timestamp,
            open=model.open,
            high=model.high,
            low=model.low,
            close=model.close,
            volume=model.volume,
        )
    
    async def log_collection(
        self,
        symbol: str,
        data_type: str,
        status: str,
        records_collected: int = 0,
        error_message: str = None,
        data_from: datetime = None,
        data_to: datetime = None,
    ) -> None:
        """Log data collection activity."""
        try:
            log = DataCollectionLog(
                exchange=self.exchange_name,
                symbol=symbol,
                timeframe=None if data_type != 'candle' else None,
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
    
    async def get_last_collected_time(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[datetime]:
        """Get timestamp of last collected candle for a pair."""
        try:
            result = await self.db_session.execute(
                select(func.max(CandleModel.timestamp))
                .where(
                    and_(
                        CandleModel.exchange == self.exchange_name,
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                    )
                )
            )
            
            last_time = result.scalar()
            return last_time
        
        except Exception as e:
            logger.error(f"Error getting last collected time: {e}")
            return None
    
    async def get_candle_count(
        self,
        symbol: str,
        timeframe: str,
    ) -> int:
        """Get total number of candles in database for a pair."""
        try:
            result = await self.db_session.execute(
                select(func.count(CandleModel.id))
                .where(
                    and_(
                        CandleModel.exchange == self.exchange_name,
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == timeframe,
                    )
                )
            )
            
            return result.scalar() or 0
        
        except Exception as e:
            logger.error(f"Error getting candle count: {e}")
            return 0
    
    def clear_cache(self, symbol: str = None, timeframe: str = None) -> None:
        """
        Clear cache.
        
        Args:
            symbol: Optional symbol to clear (clears all if None)
            timeframe: Optional timeframe to clear
        """
        if symbol is None:
            # Clear all
            self._candle_cache.clear()
            self._ticker_cache.clear()
            self._last_update.clear()
        else:
            # Clear specific symbol
            if timeframe:
                cache_key = self._get_candle_cache_key(symbol, timeframe)
                self._candle_cache.pop(cache_key, None)
            else:
                # Clear all timeframes for symbol
                keys_to_delete = [
                    k for k in self._candle_cache.keys()
                    if k.startswith(f"{self.exchange_name}_{symbol}_")
                ]
                for key in keys_to_delete:
                    del self._candle_cache[key]
            
            # Clear ticker
            ticker_key = self._get_ticker_cache_key(symbol)
            self._ticker_cache.delete(ticker_key)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "exchange": self.exchange_name,
            "candle_caches": len(self._candle_cache),
            "ticker_cache_size": len(self._ticker_cache),
            "candle_cache_keys": list(self._candle_cache.keys()),
        }
