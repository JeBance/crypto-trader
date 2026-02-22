"""Exponential Moving Average (EMA) indicator."""


class EMA:
    """
    Exponential Moving Average indicator.
    
    The EMA gives more weight to recent prices, making it more
    responsive to new information compared to SMA.
    
    Formula:
        EMA(t) = (P(t) * k) + (EMA(y) * (1 - k))
    
    Where:
        P(t) = Price today
        EMA(y) = EMA yesterday
        k = 2 / (n + 1) = smoothing factor
        n = Number of periods
    
    Example:
        >>> ema = EMA(period=20)
        >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]
        >>> ema.calculate(prices)
        45.12  # Example value
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize EMA indicator.
        
        Args:
            period: Number of periods for calculation
        """
        if period < 1:
            raise ValueError("Period must be at least 1")
        
        self.period = period
        self._multiplier = 2 / (period + 1)
        self._ema: float | None = None
    
    def calculate(self, prices: list[float]) -> float | None:
        """
        Calculate EMA value.
        
        Args:
            prices: List of prices
            
        Returns:
            EMA value or None if not enough data
        """
        if len(prices) < self.period:
            return None
        
        # Calculate initial SMA for first EMA value
        self._ema = sum(prices[:self.period]) / self.period
        
        # Calculate EMA for remaining prices
        for price in prices[self.period:]:
            self._ema = (price * self._multiplier) + (self._ema * (1 - self._multiplier))
        
        return self._ema
    
    def calculate_all(self, prices: list[float]) -> list[float | None]:
        """
        Calculate EMA for all data points.
        
        Args:
            prices: List of prices
            
        Returns:
            List of EMA values (None for insufficient data)
        """
        if len(prices) < self.period:
            return [None] * len(prices)
        
        result: list[float | None] = [None] * (self.period - 1)
        
        # First EMA is SMA
        ema = sum(prices[:self.period]) / self.period
        result.append(ema)
        
        # Calculate remaining EMAs
        for i in range(self.period, len(prices)):
            ema = (prices[i] * self._multiplier) + (ema * (1 - self._multiplier))
            result.append(ema)
        
        return result
    
    def update(self, price: float) -> float | None:
        """
        Update EMA with new price (incremental calculation).
        
        Args:
            price: New price
            
        Returns:
            Updated EMA value or None if not initialized
        """
        if self._ema is None:
            return None
        
        self._ema = (price * self._multiplier) + (self._ema * (1 - self._multiplier))
        return self._ema
    
    def reset(self) -> None:
        """Reset internal state."""
        self._ema = None
