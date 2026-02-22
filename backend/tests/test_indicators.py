"""Tests for technical indicators."""

import pytest

from app.indicators.sma import SMA
from app.indicators.ema import EMA
from app.indicators.rsi import RSI
from app.indicators.macd import MACD


class TestSMA:
    """Tests for Simple Moving Average indicator."""
    
    def test_sma_calculation(self):
        """Test SMA calculation with known values."""
        sma = SMA(period=3)
        prices = [10, 20, 30, 40, 50]
        
        # SMA of first 3: (10 + 20 + 30) / 3 = 20
        assert sma.calculate(prices[:3]) == 20.0
        
        # SMA of next 3: (20 + 30 + 40) / 3 = 30
        assert sma.calculate(prices[1:4]) == 30.0
        
        # SMA of last 3: (30 + 40 + 50) / 3 = 40
        assert sma.calculate(prices[2:5]) == 40.0
    
    def test_sma_insufficient_data(self):
        """Test SMA returns None when not enough data."""
        sma = SMA(period=5)
        prices = [10, 20, 30]  # Only 3 values, need 5
        
        assert sma.calculate(prices) is None
    
    def test_sma_calculate_all(self):
        """Test SMA calculation for all data points."""
        sma = SMA(period=3)
        prices = [10, 20, 30, 40, 50]
        result = sma.calculate_all(prices)
        
        assert result[0] is None  # Not enough data
        assert result[1] is None  # Not enough data
        assert result[2] == 20.0  # First valid SMA
        assert result[3] == 30.0
        assert result[4] == 40.0
    
    def test_sma_invalid_period(self):
        """Test SMA raises error for invalid period."""
        with pytest.raises(ValueError):
            SMA(period=0)
        
        with pytest.raises(ValueError):
            SMA(period=-1)


class TestEMA:
    """Tests for Exponential Moving Average indicator."""
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        ema = EMA(period=3)
        prices = [10, 20, 30, 40, 50]
        
        result = ema.calculate(prices)
        assert result is not None
        assert 30 <= result <= 50  # EMA should be between recent values
    
    def test_ema_insufficient_data(self):
        """Test EMA returns None when not enough data."""
        ema = EMA(period=5)
        prices = [10, 20, 30]
        
        assert ema.calculate(prices) is None
    
    def test_ema_responsive(self):
        """Test EMA is more responsive to recent prices than SMA."""
        prices = [10, 10, 10, 10, 10, 100]  # Sharp increase
        
        sma = SMA(period=5)
        ema = EMA(period=5)
        
        sma_result = sma.calculate(prices)
        ema_result = ema.calculate(prices)
        
        # EMA should be higher than SMA due to recent price spike
        assert ema_result > sma_result


class TestRSI:
    """Tests for Relative Strength Index indicator."""
    
    def test_rsi_range(self):
        """Test RSI is within 0-100 range."""
        rsi = RSI(period=14)
        prices = list(range(50, 100))  # Rising prices
        
        result = rsi.calculate(prices)
        
        assert result is not None
        assert 0 <= result <= 100
    
    def test_rsi_oversold(self):
        """Test RSI oversold detection."""
        rsi = RSI(period=14)
        
        # Falling prices should lead to oversold
        prices = [100 - i for i in range(30)]
        
        # RSI should eventually become oversold
        result = rsi.calculate(prices)
        assert result is not None
        assert result < 50  # Should be low for falling prices
    
    def test_rsi_is_overbought(self):
        """Test RSI overbought helper method."""
        rsi = RSI(period=14)
        
        # Rising prices
        prices = list(range(100))
        
        # Should detect overbought condition
        assert rsi.is_overbought(prices, threshold=70) is True
    
    def test_rsi_is_oversold(self):
        """Test RSI oversold helper method."""
        rsi = RSI(period=14)
        
        # Falling prices
        prices = list(range(100, 0, -1))
        
        # Should detect oversold condition
        assert rsi.is_oversold(prices, threshold=30) is True
    
    def test_rsi_insufficient_data(self):
        """Test RSI returns None when not enough data."""
        rsi = RSI(period=14)
        prices = [50, 51, 52]  # Only 3 values
        
        assert rsi.calculate(prices) is None


class TestMACD:
    """Tests for MACD indicator."""
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        
        # Need at least 26 + 9 = 35 values
        prices = list(range(50))
        
        result = macd.calculate(prices)
        
        assert result is not None
        assert hasattr(result, 'macd')
        assert hasattr(result, 'signal')
        assert hasattr(result, 'histogram')
    
    def test_macd_histogram(self):
        """Test MACD histogram calculation."""
        macd = MACD()
        prices = list(range(50))
        
        result = macd.calculate(prices)
        
        # Histogram = MACD line - Signal line
        assert result.histogram == result.macd - result.signal
    
    def test_macd_insufficient_data(self):
        """Test MACD returns None when not enough data."""
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        prices = list(range(20))  # Not enough
        
        assert macd.calculate(prices) is None
    
    def test_macd_crossover_detection(self):
        """Test MACD crossover detection."""
        macd = MACD()
        
        # Create prices with trend change
        prices = list(range(100))  # Strong uptrend
        
        # Should detect some crossover in strong trend
        is_bullish = macd.is_bullish_crossover(prices)
        is_bearish = macd.is_bearish_crossover(prices)
        
        # At least one should be detectable in volatile data
        assert isinstance(is_bullish, bool)
        assert isinstance(is_bearish, bool)
