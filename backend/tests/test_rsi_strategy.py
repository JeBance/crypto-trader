"""Tests for RSI strategy."""

import pytest
from datetime import datetime

from app.core.types import Candle, SignalAction
from app.strategies.rsi import RSIStrategy


@pytest.fixture
def sample_candles():
    """Create sample candle data."""
    candles = []
    base_price = 50.0
    
    for i in range(30):
        price = base_price + (i * 0.5)  # Rising prices
        candles.append(Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            timestamp=datetime.utcnow(),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price + 0.5,
            volume=1000,
        ))
    
    return candles


@pytest.fixture
def falling_candles():
    """Create falling price candle data."""
    candles = []
    base_price = 100.0
    
    for i in range(30):
        price = base_price - (i * 1.5)  # Falling prices
        candles.append(Candle(
            symbol="BTCUSDT",
            timeframe="1h",
            timestamp=datetime.utcnow(),
            open=price,
            high=price + 1,
            low=price - 2,
            close=price - 1,
            volume=1000,
        ))
    
    return candles


class TestRSIStrategy:
    """Tests for RSI trading strategy."""
    
    @pytest.mark.asyncio
    async def test_strategy_initialization(self):
        """Test strategy initializes correctly."""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        await strategy.initialize()
        
        assert strategy.is_initialized
        assert strategy.period == 14
        assert strategy.oversold == 30
        assert strategy.overbought == 70
    
    @pytest.mark.asyncio
    async def test_strategy_shutdown(self):
        """Test strategy shutdown."""
        strategy = RSIStrategy()
        await strategy.initialize()
        await strategy.shutdown()
        
        assert not strategy.is_initialized
    
    @pytest.mark.asyncio
    async def test_no_signal_when_inactive(self, sample_candles):
        """Test no signals when strategy is inactive."""
        strategy = RSIStrategy()
        await strategy.initialize()
        # Don't activate strategy
        
        for candle in sample_candles:
            signal = await strategy.on_candle(candle)
            assert signal is None
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, falling_candles):
        """Test signal generation with oversold condition."""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        await strategy.initialize()
        strategy.activate()
        
        # Process falling candles to trigger oversold
        signal = None
        for candle in falling_candles:
            result = await strategy.on_candle(candle)
            if result:
                signal = result
                break
        
        # Should generate BUY signal when oversold
        if signal:
            assert signal.action == SignalAction.BUY
            assert signal.strategy == "rsi"
            assert "rsi" in signal.metadata
    
    @pytest.mark.asyncio
    async def test_get_parameters(self):
        """Test getting strategy parameters."""
        strategy = RSIStrategy(period=14, oversold=25, overbought=75)
        
        params = strategy.get_parameters()
        
        assert params["period"] == 14
        assert params["oversold"] == 25
        assert params["overbought"] == 75
    
    @pytest.mark.asyncio
    async def test_set_parameters(self):
        """Test setting strategy parameters."""
        strategy = RSIStrategy()
        
        strategy.set_parameters({
            "period": 20,
            "oversold": 20,
            "overbought": 80,
        })
        
        assert strategy.period == 20
        assert strategy.oversold == 20
        assert strategy.overbought == 80
    
    @pytest.mark.asyncio
    async def test_reset(self, sample_candles):
        """Test strategy reset."""
        strategy = RSIStrategy()
        await strategy.initialize()
        strategy.activate()
        
        # Process some candles
        for candle in sample_candles[:20]:
            await strategy.on_candle(candle)
        
        # Reset
        strategy.reset()
        
        assert len(strategy.get_price_history()) == 0
        assert strategy.get_current_rsi() is None
    
    @pytest.mark.asyncio
    async def test_get_current_rsi(self, sample_candles):
        """Test getting current RSI value."""
        strategy = RSIStrategy(period=14)
        await strategy.initialize()
        strategy.activate()
        
        # Process enough candles
        for candle in sample_candles:
            await strategy.on_candle(candle)
        
        rsi = strategy.get_current_rsi()
        
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    @pytest.mark.asyncio
    async def test_signal_strength(self, falling_candles):
        """Test signal strength calculation."""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        await strategy.initialize()
        strategy.activate()
        
        # Process candles to find signal
        for candle in falling_candles:
            signal = await strategy.on_candle(candle)
            if signal:
                # Strength should be between 0.5 and 1.0
                assert 0.5 <= signal.strength <= 1.0
                break
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self):
        """Test strategy with insufficient data."""
        strategy = RSIStrategy(period=14)
        await strategy.initialize()
        strategy.activate()
        
        # Only 5 candles, need at least 15
        candles = [
            Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=datetime.utcnow(),
                open=50 + i,
                high=51 + i,
                low=49 + i,
                close=50.5 + i,
                volume=1000,
            )
            for i in range(5)
        ]
        
        for candle in candles:
            signal = await strategy.on_candle(candle)
            assert signal is None
