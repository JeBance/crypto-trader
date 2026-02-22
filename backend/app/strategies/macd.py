"""
MACD Trading Strategy

This strategy generates trading signals based on MACD indicator:
- MACD crosses above Signal → BUY signal
- MACD crosses below Signal → SELL signal
- Histogram divergence for strength
"""

import logging
from typing import Any

from app.core.types import Candle, Signal, SignalAction
from app.indicators.macd import MACD
from app.plugins.base import StrategyPlugin

logger = logging.getLogger(__name__)


class MACDStrategy(StrategyPlugin):
    """
    MACD trading strategy.
    
    Uses MACD indicator to generate signals:
    - MACD Line crosses above Signal Line → BUY
    - MACD Line crosses below Signal Line → SELL
    - Histogram confirms momentum
    
    Configuration parameters:
    - fast_period: Fast EMA period (default: 12)
    - slow_period: Slow EMA period (default: 26)
    - signal_period: Signal EMA period (default: 9)
    
    Example:
        >>> strategy = MACDStrategy(
        ...     fast_period=12,
        ...     slow_period=26,
        ...     signal_period=9
        ... )
        >>> await strategy.initialize()
        >>> signal = await strategy.on_candle(candle)
    """
    
    name = "macd"
    version = "1.0.0"
    description = "MACD crossover trading strategy"
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        config: dict | None = None,
    ):
        # Merge provided config with defaults
        merged_config = config or {}
        merged_config.setdefault("fast_period", fast_period)
        merged_config.setdefault("slow_period", slow_period)
        merged_config.setdefault("signal_period", signal_period)
        
        super().__init__(merged_config)
        
        self.fast_period = merged_config["fast_period"]
        self.slow_period = merged_config["slow_period"]
        self.signal_period = merged_config["signal_period"]
        
        # Initialize MACD indicator
        self._macd = MACD(
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period,
        )
        
        self._prices: list[float] = []
        self._prev_macd: float | None = None
        self._prev_signal: float | None = None
        self._last_signal: Signal | None = None
    
    async def initialize(self) -> None:
        """Initialize the strategy."""
        logger.info(
            f"Initializing MACD Strategy "
            f"(fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period})"
        )
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the strategy."""
        logger.info("Shutting down MACD Strategy")
        self._initialized = False
        self.reset()
    
    async def on_candle(self, candle: Candle) -> Signal | None:
        """
        Process a new candle and generate signal if MACD crossover detected.
        
        Args:
            candle: New candle data
            
        Returns:
            Trading signal or None
        """
        if not self._active:
            return None
        
        # Add close price to history
        self._prices.append(candle.close)
        
        # Need enough data for MACD calculation
        min_length = self.slow_period + self.signal_period + 5
        if len(self._prices) < min_length:
            return None
        
        # Calculate MACD
        macd_result = self._macd.calculate(self._prices)
        
        if macd_result is None:
            return None
        
        current_macd = macd_result.macd
        current_signal = macd_result.signal
        current_histogram = macd_result.histogram
        
        signal = None
        
        # Check for crossovers (need previous values)
        if self._prev_macd is not None and self._prev_signal is not None:
            # Bullish crossover: MACD crosses above Signal
            if self._prev_macd <= self._prev_signal and current_macd > current_signal:
                signal = Signal(
                    action=SignalAction.BUY,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_macd, current_signal, "bullish"),
                    price=candle.close,
                    metadata={
                        "macd": current_macd,
                        "signal": current_signal,
                        "histogram": current_histogram,
                        "crossover": "bullish",
                    },
                )
                logger.info(
                    f"🟢 MACD Bullish Crossover: {candle.symbol} - "
                    f"MACD ({current_macd:.4f}) > Signal ({current_signal:.4f})"
                )
            
            # Bearish crossover: MACD crosses below Signal
            elif self._prev_macd >= self._prev_signal and current_macd < current_signal:
                signal = Signal(
                    action=SignalAction.SELL,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_macd, current_signal, "bearish"),
                    price=candle.close,
                    metadata={
                        "macd": current_macd,
                        "signal": current_signal,
                        "histogram": current_histogram,
                        "crossover": "bearish",
                    },
                )
                logger.info(
                    f"🔴 MACD Bearish Crossover: {candle.symbol} - "
                    f"MACD ({current_macd:.4f}) < Signal ({current_signal:.4f})"
                )
        
        # Store current values for next comparison
        self._prev_macd = current_macd
        self._prev_signal = current_signal
        
        if signal:
            self._last_signal = signal
        
        return signal
    
    def _calculate_strength(
        self,
        macd: float,
        signal: float,
        direction: str,
    ) -> float:
        """
        Calculate signal strength based on MACD divergence and histogram.
        
        Args:
            macd: MACD line value
            signal: Signal line value
            direction: 'bullish' or 'bearish'
            
        Returns:
            Signal strength (0.5 - 1.0)
        """
        # Calculate divergence
        divergence = abs(macd - signal)
        
        # Stronger signal with larger divergence
        # Typical divergence: 0.001 - 0.01
        strength = 0.5 + min(divergence * 50, 0.5)
        
        return min(1.0, max(0.5, strength))
    
    def get_parameters(self) -> dict[str, Any]:
        """Get strategy parameters."""
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "signal_period": self.signal_period,
        }
    
    def set_parameters(self, params: dict[str, Any]) -> None:
        """Set strategy parameters."""
        if "fast_period" in params:
            self.fast_period = params["fast_period"]
        
        if "slow_period" in params:
            self.slow_period = params["slow_period"]
        
        if "signal_period" in params:
            self.signal_period = params["signal_period"]
        
        # Reinitialize MACD with new parameters
        self._macd = MACD(
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            signal_period=self.signal_period,
        )
        
        # Update config
        self.config.update(params)
        logger.info(f"MACD Strategy parameters updated: {params}")
    
    def reset(self) -> None:
        """Reset strategy state."""
        self._prices.clear()
        self._prev_macd = None
        self._prev_signal = None
        self._last_signal = None
        self._macd.reset()
    
    def get_current_macd(self) -> dict[str, float | None]:
        """Get current MACD values."""
        if len(self._prices) < self.slow_period + self.signal_period:
            return {"macd": None, "signal": None, "histogram": None}
        
        result = self._macd.calculate(self._prices)
        
        if result is None:
            return {"macd": None, "signal": None, "histogram": None}
        
        return {
            "macd": result.macd,
            "signal": result.signal,
            "histogram": result.histogram,
        }
    
    def get_price_history(self) -> list[float]:
        """Get price history."""
        return self._prices.copy()
