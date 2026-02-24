"""RSI-based trading strategy."""

import logging
from typing import Any

from app.core.types import Candle, Signal, SignalAction
from app.indicators.rsi import RSI
from app.plugins.base import StrategyPlugin

logger = logging.getLogger(__name__)


class RSIStrategy(StrategyPlugin):
    """
    RSI (Relative Strength Index) trading strategy.
    
    This strategy generates trading signals based on RSI overbought/oversold levels:
    - Buy signal when RSI crosses below oversold level (typically 30)
    - Sell signal when RSI crosses above overbought level (typically 70)
    
    Configuration parameters:
    - period: RSI calculation period (default: 14)
    - oversold: Oversold threshold (default: 30)
    - overbought: Overbought threshold (default: 70)
    
    Example:
        >>> strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        >>> await strategy.initialize()
        >>> signal = await strategy.on_candle(candle)
    """
    
    name = "rsi"
    version = "1.0.0"
    description = "RSI overbought/oversold trading strategy"
    
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        config: dict | None = None,
    ):
        # Merge provided config with defaults
        merged_config = config or {}
        merged_config.setdefault("period", period)
        merged_config.setdefault("oversold", oversold)
        merged_config.setdefault("overbought", overbought)
        
        super().__init__(merged_config)
        
        self.period = merged_config["period"]
        self.oversold = oversold
        self.overbought = overbought
        
        self._rsi = RSI(period=self.period)
        self._prices: list[float] = []
        self._prev_rsi: float | None = None
        self._last_signal: Signal | None = None
    
    async def initialize(self) -> None:
        """Initialize the strategy."""
        logger.info(f"Initializing RSI Strategy (period={self.period}, oversold={self.oversold}, overbought={self.overbought})")
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the strategy."""
        logger.info("Shutting down RSI Strategy")
        self._initialized = False
        self.reset()
    
    async def on_candle(self, candle: Candle) -> Signal | None:
        """
        Process a new candle and generate signal if conditions are met.
        
        Args:
            candle: New candle data
            
        Returns:
            Trading signal or None
        """
        if not self._active:
            return None
        
        # Add close price to history
        self._prices.append(candle.close)
        
        # Need at least period + 1 candles for RSI calculation
        if len(self._prices) < self.period + 1:
            return None
        
        # Calculate current RSI
        current_rsi = self._rsi.calculate(self._prices)
        
        if current_rsi is None:
            return None
        
        signal = None
        
        # Check for oversold condition (buy signal)
        # RSI crossed below oversold level
        if self._prev_rsi is not None:
            if self._prev_rsi >= self.oversold and current_rsi < self.oversold:
                signal = Signal(
                    action=SignalAction.BUY,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_rsi, self.oversold, True),
                    price=candle.close,
                    metadata={
                        "rsi": current_rsi,
                        "condition": "oversold",
                        "threshold": self.oversold,
                    },
                )
                logger.info(f"RSI Buy signal: {candle.symbol} - RSI={current_rsi:.2f}")
            
            # Check for overbought condition (sell signal)
            # RSI crossed above overbought level
            elif self._prev_rsi <= self.overbought and current_rsi > self.overbought:
                signal = Signal(
                    action=SignalAction.SELL,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_rsi, self.overbought, False),
                    price=candle.close,
                    metadata={
                        "rsi": current_rsi,
                        "condition": "overbought",
                        "threshold": self.overbought,
                    },
                )
                logger.info(f"RSI Sell signal: {candle.symbol} - RSI={current_rsi:.2f}")
        
        # Store current RSI for next comparison
        self._prev_rsi = current_rsi
        
        if signal:
            self._last_signal = signal
        
        return signal
    
    def _calculate_strength(self, rsi: float, threshold: float, is_oversold: bool) -> float:
        """
        Calculate signal strength based on RSI deviation from threshold.
        
        Args:
            rsi: Current RSI value
            threshold: Threshold level
            is_oversold: Whether checking oversold condition
            
        Returns:
            Signal strength (0.0 - 1.0)
        """
        if is_oversold:
            # Stronger signal when RSI is lower
            deviation = threshold - rsi
            max_deviation = threshold  # Max deviation is threshold itself
        else:
            # Stronger signal when RSI is higher
            deviation = rsi - threshold
            max_deviation = 100 - threshold  # Max deviation is 100 - threshold
        
        # Normalize to 0-1 range, with minimum 0.5 at threshold crossing
        strength = 0.5 + (deviation / max_deviation) * 0.5
        return min(1.0, max(0.5, strength))
    
    def get_parameters(self) -> dict[str, Any]:
        """Get strategy parameters."""
        return {
            "period": self.period,
            "oversold": self.oversold,
            "overbought": self.overbought,
        }
    
    def set_parameters(self, params: dict[str, Any]) -> None:
        """Set strategy parameters."""
        if "period" in params:
            self.period = params["period"]
            self._rsi = RSI(period=self.period)
        
        if "oversold" in params:
            self.oversold = params["oversold"]
        
        if "overbought" in params:
            self.overbought = params["overbought"]
        
        # Update config
        self.config.update(params)
        logger.info(f"RSI Strategy parameters updated: {params}")
    
    def reset(self) -> None:
        """Reset strategy state."""
        self._prices.clear()
        self._prev_rsi = None
        self._last_signal = None
        self._rsi.reset()
    
    def get_current_rsi(self) -> float | None:
        """Get current RSI value."""
        if len(self._prices) < self.period + 1:
            return None
        return self._rsi.calculate(self._prices)
    
    def get_price_history(self) -> list[float]:
        """Get price history."""
        return self._prices.copy()
