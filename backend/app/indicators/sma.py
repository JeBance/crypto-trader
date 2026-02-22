"""Simple Moving Average (SMA) indicator."""


class SMA:
    """
    Simple Moving Average indicator.
    
    The SMA is calculated by taking the arithmetic mean of 
    a given set of prices over a specified number of periods.
    
    Formula:
        SMA = (P1 + P2 + ... + Pn) / n
    
    Where:
        P = Price for period i
        n = Number of periods
    
    Example:
        >>> sma = SMA(period=20)
        >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]
        >>> sma.calculate(prices)
        None  # Not enough data
        >>> sma.calculate(prices + [46.5, 47.0, 47.5, 48.0, 48.5, 49.0, 49.5, 50.0, 50.5, 51.0])
        47.75  # Example value
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.
        
        Args:
            period: Number of periods for calculation
        """
        if period < 1:
            raise ValueError("Period must be at least 1")
        
        self.period = period
        self._values: list[float] = []
    
    def calculate(self, prices: list[float]) -> float | None:
        """
        Calculate SMA value.
        
        Args:
            prices: List of prices (at least 'period' values)
            
        Returns:
            SMA value or None if not enough data
        """
        if len(prices) < self.period:
            return None
        
        # Take last 'period' values
        recent_prices = prices[-self.period:]
        return sum(recent_prices) / self.period
    
    def calculate_all(self, prices: list[float]) -> list[float | None]:
        """
        Calculate SMA for all data points.
        
        Args:
            prices: List of prices
            
        Returns:
            List of SMA values (None for insufficient data)
        """
        result: list[float | None] = []
        
        for i in range(len(prices)):
            if i < self.period - 1:
                result.append(None)
            else:
                sma_value = sum(prices[i - self.period + 1:i + 1]) / self.period
                result.append(sma_value)
        
        return result
    
    def reset(self) -> None:
        """Reset internal state."""
        self._values.clear()
