"""Relative Strength Index (RSI) indicator."""


class RSI:
    """
    Relative Strength Index indicator.
    
    RSI is a momentum oscillator that measures the speed and change
    of price movements. It ranges from 0 to 100.
    
    Traditional interpretation:
    - RSI > 70: Overbought (potential sell signal)
    - RSI < 30: Oversold (potential buy signal)
    
    Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
    
    Where averages are calculated using Wilder's smoothing method.
    
    Example:
        >>> rsi = RSI(period=14)
        >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08]
        >>> rsi.calculate(prices)
        None  # Not enough data
    """
    
    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.
        
        Args:
            period: Number of periods for calculation (default 14)
        """
        if period < 2:
            raise ValueError("Period must be at least 2")
        
        self.period = period
        self._avg_gain: float | None = None
        self._avg_loss: float | None = None
    
    def calculate(self, prices: list[float]) -> float | None:
        """
        Calculate RSI value.
        
        Args:
            prices: List of prices (at least 'period' + 1 values)
            
        Returns:
            RSI value (0-100) or None if not enough data
        """
        if len(prices) < self.period + 1:
            return None
        
        # Calculate price changes
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(0, change) for change in changes]
        losses = [max(0, -change) for change in changes]
        
        # Calculate initial average gain and loss using simple average
        if self._avg_gain is None or self._avg_loss is None:
            self._avg_gain = sum(gains[:self.period]) / self.period
            self._avg_loss = sum(losses[:self.period]) / self.period
            
            # Use Wilder's smoothing for remaining values
            for i in range(self.period, len(gains)):
                self._avg_gain = (self._avg_gain * (self.period - 1) + gains[i]) / self.period
                self._avg_loss = (self._avg_loss * (self.period - 1) + losses[i]) / self.period
        else:
            # Continue with Wilder's smoothing
            for i in range(len(gains)):
                self._avg_gain = (self._avg_gain * (self.period - 1) + gains[i]) / self.period
                self._avg_loss = (self._avg_loss * (self.period - 1) + losses[i]) / self.period
        
        # Calculate RSI
        if self._avg_loss == 0:
            return 100.0
        
        rs = self._avg_gain / self._avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_all(self, prices: list[float]) -> list[float | None]:
        """
        Calculate RSI for all data points.
        
        Args:
            prices: List of prices
            
        Returns:
            List of RSI values (None for insufficient data)
        """
        if len(prices) < self.period + 1:
            return [None] * len(prices)
        
        result: list[float | None] = [None] * self.period
        
        # Calculate price changes
        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(0, change) for change in changes]
        losses = [max(0, -change) for change in changes]
        
        # First RSI calculation
        avg_gain = sum(gains[:self.period]) / self.period
        avg_loss = sum(losses[:self.period]) / self.period
        
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))
        
        # Calculate remaining RSIs using Wilder's smoothing
        for i in range(self.period, len(gains)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period
            
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100 - (100 / (1 + rs)))
        
        return result
    
    def is_overbought(self, prices: list[float], threshold: float = 70.0) -> bool:
        """
        Check if RSI indicates overbought condition.
        
        Args:
            prices: List of prices
            threshold: Overbought threshold (default 70)
            
        Returns:
            True if overbought
        """
        rsi = self.calculate(prices)
        return rsi is not None and rsi > threshold
    
    def is_oversold(self, prices: list[float], threshold: float = 30.0) -> bool:
        """
        Check if RSI indicates oversold condition.
        
        Args:
            prices: List of prices
            threshold: Oversold threshold (default 30)
            
        Returns:
            True if oversold
        """
        rsi = self.calculate(prices)
        return rsi is not None and rsi < threshold
    
    def reset(self) -> None:
        """Reset internal state."""
        self._avg_gain = None
        self._avg_loss = None
