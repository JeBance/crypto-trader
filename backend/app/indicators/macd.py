"""Moving Average Convergence Divergence (MACD) indicator."""

from dataclasses import dataclass

from app.indicators.ema import EMA


@dataclass
class MACDValue:
    """MACD calculation result."""
    macd: float
    signal: float
    histogram: float
    
    def __repr__(self) -> str:
        return f"MACDValue(macd={self.macd:.4f}, signal={self.signal:.4f}, histogram={self.histogram:.4f})"


class MACD:
    """
    Moving Average Convergence Divergence indicator.
    
    MACD is a trend-following momentum indicator that shows the
    relationship between two moving averages of a price.
    
    Components:
    - MACD Line: (12-period EMA - 26-period EMA)
    - Signal Line: 9-period EMA of MACD Line
    - Histogram: MACD Line - Signal Line
    
    Traditional interpretation:
    - MACD crosses above signal: Bullish (buy signal)
    - MACD crosses below signal: Bearish (sell signal)
    - Positive histogram: Bullish momentum
    - Negative histogram: Bearish momentum
    
    Example:
        >>> macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        >>> prices = [44, 44.34, 44.09, ...]  # At least 26 + 9 values
        >>> result = macd.calculate(prices)
        MACDValue(macd=0.1234, signal=0.0987, histogram=0.0247)
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        Initialize MACD indicator.
        
        Args:
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
        """
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self._fast_ema = EMA(fast_period)
        self._slow_ema = EMA(slow_period)
        self._signal_ema = EMA(signal_period)
        self._macd_values: list[float] = []
    
    def calculate(self, prices: list[float]) -> MACDValue | None:
        """
        Calculate MACD value.
        
        Args:
            prices: List of prices (at least slow_period + signal_period values)
            
        Returns:
            MACDValue or None if not enough data
        """
        min_length = self.slow_period + self.signal_period
        
        if len(prices) < min_length:
            return None
        
        # Calculate MACD line values
        macd_line_values = []
        
        for i in range(len(prices)):
            fast_ema = self._fast_ema.calculate(prices[:i + 1])
            slow_ema = self._slow_ema.calculate(prices[:i + 1])
            
            if fast_ema is not None and slow_ema is not None:
                macd_line_values.append(fast_ema - slow_ema)
        
        if len(macd_line_values) < self.signal_period:
            return None
        
        # Calculate signal line (EMA of MACD line)
        signal_line = self._signal_ema.calculate(macd_line_values)
        
        if signal_line is None:
            return None
        
        # Get current MACD line value
        macd_line = macd_line_values[-1]
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return MACDValue(
            macd=macd_line,
            signal=signal_line,
            histogram=histogram,
        )
    
    def calculate_all(self, prices: list[float]) -> list[MACDValue | None]:
        """
        Calculate MACD for all data points.
        
        Args:
            prices: List of prices
            
        Returns:
            List of MACDValue (None for insufficient data)
        """
        result: list[MACDValue | None] = []
        
        for i in range(len(prices)):
            result.append(self.calculate(prices[:i + 1]))
        
        return result
    
    def is_bullish_crossover(self, prices: list[float]) -> bool:
        """
        Check for bullish crossover (MACD crosses above signal).
        
        Args:
            prices: List of prices
            
        Returns:
            True if bullish crossover detected
        """
        if len(prices) < self.slow_period + self.signal_period + 1:
            return False
        
        # Current values
        current = self.calculate(prices)
        
        # Previous values
        previous = self.calculate(prices[:-1])
        
        if current is None or previous is None:
            return False
        
        # Check for crossover: MACD was below signal, now above
        return (previous.macd <= previous.signal) and (current.macd > current.signal)
    
    def is_bearish_crossover(self, prices: list[float]) -> bool:
        """
        Check for bearish crossover (MACD crosses below signal).
        
        Args:
            prices: List of prices
            
        Returns:
            True if bearish crossover detected
        """
        if len(prices) < self.slow_period + self.signal_period + 1:
            return False
        
        # Current values
        current = self.calculate(prices)
        
        # Previous values
        previous = self.calculate(prices[:-1])
        
        if current is None or previous is None:
            return False
        
        # Check for crossover: MACD was above signal, now below
        return (previous.macd >= previous.signal) and (current.macd < current.signal)
    
    def reset(self) -> None:
        """Reset internal state."""
        self._fast_ema.reset()
        self._slow_ema.reset()
        self._signal_ema.reset()
        self._macd_values.clear()
