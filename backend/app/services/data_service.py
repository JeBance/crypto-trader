"""Data Service for market data retrieval and caching."""

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.types import Candle, Ticker
from app.plugins.base import ExchangePlugin

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


class DataService:
    """
    Service for retrieving and caching market data.
    
    Provides cached access to candle and ticker data from exchanges.
    
    Example:
        >>> service = DataService(exchange)
        >>> candles = await service.get_candles("BTCUSDT", "1h", limit=100)
        >>> ticker = await service.get_ticker("BTCUSDT")
    """
    
    def __init__(self, exchange: ExchangePlugin, cache_size: int = 1000):
        self.exchange = exchange
        self._candle_cache: Dict[str, LRUCache] = {}  # symbol_timeframe -> LRUCache
        self._ticker_cache: LRUCache = LRUCache(cache_size)
        self._last_update: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=30)  # Cache TTL for tickers
    
    def _get_candle_cache_key(self, symbol: str, timeframe: str) -> str:
        """Generate cache key for candles."""
        return f"{symbol}_{timeframe}"
    
    def _get_ticker_cache_key(self, symbol: str) -> str:
        """Generate cache key for ticker."""
        return symbol
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        use_cache: bool = True,
    ) -> List[Candle]:
        """
        Get candlestick data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            limit: Number of candles to retrieve
            use_cache: Whether to use cache
            
        Returns:
            List of candles
        """
        cache_key = self._get_candle_cache_key(symbol, timeframe)
        
        # Check cache
        if use_cache and cache_key in self._candle_cache:
            cached = self._candle_cache[cache_key].get("candles")
            if cached:
                logger.debug(f"Cache hit for {symbol} {timeframe}")
                return cached
        
        # Fetch from exchange
        logger.debug(f"Fetching candles for {symbol} {timeframe}")
        candles = await self.exchange.get_candles(symbol, timeframe, limit)
        
        # Update cache
        if cache_key not in self._candle_cache:
            self._candle_cache[cache_key] = LRUCache(10)
        
        self._candle_cache[cache_key].set("candles", candles)
        self._candle_cache[cache_key].set("timestamp", datetime.utcnow())
        
        return candles
    
    async def get_ticker(self, symbol: str, use_cache: bool = True) -> Optional[Ticker]:
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
                if datetime.utcnow() - last_update < self._cache_ttl:
                    logger.debug(f"Cache hit for ticker {symbol}")
                    return cached
        
        # Fetch from exchange
        logger.debug(f"Fetching ticker for {symbol}")
        ticker = await self.exchange.get_ticker(symbol)
        
        # Update cache
        self._ticker_cache.set(cache_key, ticker)
        self._last_update[cache_key] = datetime.utcnow()
        
        return ticker
    
    async def get_latest_candle(
        self,
        symbol: str,
        timeframe: str,
    ) -> Optional[Candle]:
        """
        Get the latest candle.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            
        Returns:
            Latest candle or None
        """
        candles = await self.get_candles(symbol, timeframe, limit=1, use_cache=True)
        return candles[-1] if candles else None
    
    async def refresh_candles(
        self,
        symbol: str,
        timeframe: str,
    ) -> List[Candle]:
        """
        Force refresh candle data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            
        Returns:
            Updated list of candles
        """
        cache_key = self._get_candle_cache_key(symbol, timeframe)
        
        # Clear cache for this symbol/timeframe
        if cache_key in self._candle_cache:
            self._candle_cache[cache_key].clear()
        
        # Fetch fresh data
        return await self.get_candles(symbol, timeframe, use_cache=False)
    
    async def get_historical_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime = None,
    ) -> List[Candle]:
        """
        Get historical candles between two dates.
        
        Note: This is a simplified implementation. Real implementation
        would need to handle pagination for large date ranges.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe
            start_time: Start datetime
            end_time: End datetime (default: now)
            
        Returns:
            List of historical candles
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Calculate approximate number of candles needed
        delta = end_time - start_time
        timeframe_hours = {
            "1m": 1/60, "5m": 5/60, "15m": 15/60, "30m": 0.5,
            "1h": 1, "4h": 4, "1d": 24,
        }
        hours_per_candle = timeframe_hours.get(timeframe, 1)
        approx_candles = int(delta.total_seconds() / 3600 / hours_per_candle)
        
        # Fetch candles (limit to 1000 per request)
        limit = min(approx_candles, 1000)
        candles = await self.get_candles(symbol, timeframe, limit=limit)
        
        # Filter by date range
        filtered = [
            c for c in candles
            if start_time <= c.timestamp <= end_time
        ]
        
        return filtered
    
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
                    if k.startswith(f"{symbol}_")
                ]
                for key in keys_to_delete:
                    del self._candle_cache[key]
            
            # Clear ticker
            ticker_key = self._get_ticker_cache_key(symbol)
            self._ticker_cache.delete(ticker_key)
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "candle_caches": len(self._candle_cache),
            "ticker_cache_size": len(self._ticker_cache),
            "candle_cache_keys": list(self._candle_cache.keys()),
        }
