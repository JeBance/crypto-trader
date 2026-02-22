"""Tests for Data Service and LRU Cache."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.data_service import DataService, LRUCache
from app.core.types import Candle, Ticker


class TestLRUCache:
    """Tests for LRU Cache."""
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = LRUCache(max_size=5)
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_default(self):
        """Test get with default value."""
        cache = LRUCache(max_size=5)
        
        result = cache.get("nonexistent", "default")
        assert result == "default"
    
    def test_max_size(self):
        """Test cache respects max size."""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1
        
        assert len(cache) == 3
        assert "key1" not in cache
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"
    
    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = LRUCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new key, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert "key1" in cache  # Still there (was accessed)
        assert "key2" not in cache  # Evicted
        assert "key3" in cache
        assert "key4" in cache
    
    def test_delete(self):
        """Test delete operation."""
        cache = LRUCache(max_size=5)
        
        cache.set("key1", "value1")
        cache.delete("key1")
        
        assert "key1" not in cache
    
    def test_clear(self):
        """Test clear operation."""
        cache = LRUCache(max_size=5)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert len(cache) == 0
    
    def test_contains(self):
        """Test contains operator."""
        cache = LRUCache(max_size=5)
        
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache
    
    def test_len(self):
        """Test length operator."""
        cache = LRUCache(max_size=5)
        
        assert len(cache) == 0
        
        cache.set("key1", "value1")
        assert len(cache) == 1
        
        cache.set("key2", "value2")
        assert len(cache) == 2


class TestDataService:
    """Tests for Data Service."""
    
    @pytest.fixture
    def mock_exchange(self):
        """Create mock exchange."""
        exchange = AsyncMock()
        
        # Mock get_candles
        async def mock_get_candles(symbol, timeframe, limit=100):
            return [
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.utcnow() - timedelta(minutes=i),
                    open=50000 - i,
                    high=50100 - i,
                    low=49900 - i,
                    close=50050 - i,
                    volume=1000,
                )
                for i in range(limit)
            ]
        
        exchange.get_candles = mock_get_candles
        
        # Mock get_ticker
        async def mock_get_ticker(symbol):
            return Ticker(
                symbol=symbol,
                last_price=50000,
                bid=49999,
                ask=50001,
                high_24h=51000,
                low_24h=49000,
                volume_24h=1000000,
                change_24h=1000,
                change_percent_24h=2.0,
            )
        
        exchange.get_ticker = mock_get_ticker
        
        return exchange
    
    @pytest.mark.asyncio
    async def test_get_candles(self, mock_exchange):
        """Test getting candles."""
        service = DataService(mock_exchange)
        
        candles = await service.get_candles("BTCUSDT", "1h", limit=50)
        
        assert len(candles) == 50
        assert all(isinstance(c, Candle) for c in candles)
        assert candles[0].symbol == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_get_candles_cache(self, mock_exchange):
        """Test candle caching."""
        service = DataService(mock_exchange)
        
        # First call - should fetch from exchange
        candles1 = await service.get_candles("BTCUSDT", "1h")
        
        # Second call - should use cache
        candles2 = await service.get_candles("BTCUSDT", "1h", use_cache=True)
        
        # Should be same objects (from cache)
        assert candles1 is candles2
    
    @pytest.mark.asyncio
    async def test_get_ticker(self, mock_exchange):
        """Test getting ticker."""
        service = DataService(mock_exchange)
        
        ticker = await service.get_ticker("BTCUSDT")
        
        assert isinstance(ticker, Ticker)
        assert ticker.symbol == "BTCUSDT"
        assert ticker.last_price == 50000
    
    @pytest.mark.asyncio
    async def test_get_ticker_cache_ttl(self, mock_exchange):
        """Test ticker cache TTL."""
        service = DataService(mock_exchange, cache_size=100)
        
        # First call
        ticker1 = await service.get_ticker("BTCUSDT")
        
        # Immediate second call - should use cache
        ticker2 = await service.get_ticker("BTCUSDT", use_cache=True)
        
        assert ticker1 is ticker2  # Same object from cache
    
    @pytest.mark.asyncio
    async def test_get_latest_candle(self, mock_exchange):
        """Test getting latest candle."""
        service = DataService(mock_exchange)
        
        candle = await service.get_latest_candle("BTCUSDT", "1h")
        
        assert isinstance(candle, Candle)
    
    @pytest.mark.asyncio
    async def test_refresh_candles(self, mock_exchange):
        """Test refreshing candles (bypass cache)."""
        service = DataService(mock_exchange)
        
        # First call - cached
        candles1 = await service.get_candles("BTCUSDT", "1h")
        
        # Refresh - should fetch fresh data
        candles2 = await service.refresh_candles("BTCUSDT", "1h")
        
        assert candles2 is not candles1  # Different objects
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, mock_exchange):
        """Test clearing cache."""
        service = DataService(mock_exchange)
        
        # Populate cache
        await service.get_candles("BTCUSDT", "1h")
        await service.get_ticker("BTCUSDT")
        
        stats_before = service.get_cache_stats()
        assert stats_before["candle_caches"] > 0
        
        # Clear all
        service.clear_cache()
        
        stats_after = service.get_cache_stats()
        assert stats_after["candle_caches"] == 0
    
    @pytest.mark.asyncio
    async def test_clear_cache_specific_symbol(self, mock_exchange):
        """Test clearing cache for specific symbol."""
        service = DataService(mock_exchange)
        
        # Populate cache for multiple symbols
        await service.get_candles("BTCUSDT", "1h")
        await service.get_candles("ETHUSDT", "1h")
        
        # Clear only BTCUSDT
        service.clear_cache(symbol="BTCUSDT")
        
        stats = service.get_cache_stats()
        assert "BTCUSDT_1h" not in stats["candle_cache_keys"]
        assert "ETHUSDT_1h" in stats["candle_cache_keys"]
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, mock_exchange):
        """Test getting cache statistics."""
        service = DataService(mock_exchange)
        
        await service.get_candles("BTCUSDT", "1h")
        await service.get_ticker("BTCUSDT")
        
        stats = service.get_cache_stats()
        
        assert "candle_caches" in stats
        assert "ticker_cache_size" in stats
        assert "candle_cache_keys" in stats
        assert stats["ticker_cache_size"] >= 1
