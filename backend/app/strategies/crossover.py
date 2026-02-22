"""
Crossover Trading Strategy (SMA/EMA)

This strategy generates trading signals when two moving averages cross:
- Fast MA crosses above Slow MA → BUY signal
- Fast MA crosses below Slow MA → SELL signal

Supports both SMA and EMA calculations.
"""

import logging
from typing import Any, Literal

from app.core.types import Candle, Signal, SignalAction
from app.indicators.sma import SMA
from app.indicators.ema import EMA
from app.plugins.base import StrategyPlugin

logger = logging.getLogger(__name__)


class CrossoverStrategy(StrategyPlugin):
    """
    Crossover trading strategy.
    
    Uses two moving averages (fast and slow) to generate signals:
    - Golden Cross: Fast MA crosses above Slow MA → BUY
    - Death Cross: Fast MA crosses below Slow MA → SELL
    
    Configuration parameters:
    - fast_period: Fast MA period (default: 9)
    - slow_period: Slow MA period (default: 21)
    - ma_type: MA type 'sma' or 'ema' (default: 'ema')
    
    Example:
        >>> strategy = CrossoverStrategy(
        ...     fast_period=9,
        ...     slow_period=21,
        ...     ma_type='ema'
        ... )
        >>> await strategy.initialize()
        >>> signal = await strategy.on_candle(candle)
    """
    
    name = "crossover"
    version = "1.0.0"
    description = "Moving Average Crossover strategy (SMA/EMA)"
    
    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
        ma_type: Literal["sma", "ema"] = "ema",
        config: dict | None = None,
    ):
        # Merge provided config with defaults
        merged_config = config or {}
        merged_config.setdefault("fast_period", fast_period)
        merged_config.setdefault("slow_period", slow_period)
        merged_config.setdefault("ma_type", ma_type)
        
        super().__init__(merged_config)
        
        self.fast_period = merged_config["fast_period"]
        self.slow_period = merged_config["slow_period"]
        self.ma_type = merged_config["ma_type"]
        
        # Validate periods
        if self.fast_period >= self.slow_period:
            raise ValueError(
                f"Fast period ({fast_period}) must be less than "
                f"slow period ({slow_period})"
            )
        
        # Initialize indicators
        if self.ma_type == "ema":
            self._fast_ma = EMA(period=self.fast_period)
            self._slow_ma = EMA(period=self.slow_period)
        else:
            self._fast_ma = SMA(period=self.fast_period)
            self._slow_ma = SMA(period=self.slow_period)
        
        self._prices: list[float] = []
        self._prev_fast_ma: float | None = None
        self._prev_slow_ma: float | None = None
        self._last_signal: Signal | None = None
    
    async def initialize(self) -> None:
        """Initialize the strategy."""
        logger.info(
            f"Initializing Crossover Strategy "
            f"(fast={self.fast_period}, slow={self.slow_period}, type={self.ma_type})"
        )
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the strategy."""
        logger.info("Shutting down Crossover Strategy")
        self._initialized = False
        self.reset()
    
    async def on_candle(self, candle: Candle) -> Signal | None:
        """
        Process a new candle and generate signal if crossover detected.
        
        Args:
            candle: New candle data
            
        Returns:
            Trading signal or None
        """
        if not self._active:
            return None
        
        # Add close price to history
        self._prices.append(candle.close)
        
        # Need enough data for both MAs
        if len(self._prices) < self.slow_period:
            return None
        
        # Calculate current MAs
        current_fast_ma = self._fast_ma.calculate(self._prices)
        current_slow_ma = self._slow_ma.calculate(self._prices)
        
        if current_fast_ma is None or current_slow_ma is None:
            return None
        
        signal = None
        
        # Check for crossovers (need previous values)
        if self._prev_fast_ma is not None and self._prev_slow_ma is not None:
            # Golden Cross: Fast MA crosses above Slow MA
            if (self._prev_fast_ma <= self._prev_slow_ma and 
                current_fast_ma > current_slow_ma):
                
                signal = Signal(
                    action=SignalAction.BUY,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_fast_ma, current_slow_ma, "bullish"),
                    price=candle.close,
                    metadata={
                        "fast_ma": current_fast_ma,
                        "slow_ma": current_slow_ma,
                        "crossover": "golden_cross",
                        "ma_type": self.ma_type,
                    },
                )
                logger.info(
                    f"🟢 Golden Cross detected: {candle.symbol} - "
                    f"Fast MA ({current_fast_ma:.2f}) > Slow MA ({current_slow_ma:.2f})"
                )
            
            # Death Cross: Fast MA crosses below Slow MA
            elif (self._prev_fast_ma >= self._prev_slow_ma and 
                  current_fast_ma < current_slow_ma):
                
                signal = Signal(
                    action=SignalAction.SELL,
                    symbol=candle.symbol,
                    strategy=self.name,
                    strength=self._calculate_strength(current_fast_ma, current_slow_ma, "bearish"),
                    price=candle.close,
                    metadata={
                        "fast_ma": current_fast_ma,
                        "slow_ma": current_slow_ma,
                        "crossover": "death_cross",
                        "ma_type": self.ma_type,
                    },
                )
                logger.info(
                    f"🔴 Death Cross detected: {candle.symbol} - "
                    f"Fast MA ({current_fast_ma:.2f}) < Slow MA ({current_slow_ma:.2f})"
                )
        
        # Store current MAs for next comparison
        self._prev_fast_ma = current_fast_ma
        self._prev_slow_ma = current_slow_ma
        
        if signal:
            self._last_signal = signal
        
        return signal
    
    def _calculate_strength(
        self,
        fast_ma: float,
        slow_ma: float,
        direction: str,
    ) -> float:
        """
        Calculate signal strength based on MA divergence.
        
        Args:
            fast_ma: Fast MA value
            slow_ma: Slow MA value
            direction: 'bullish' or 'bearish'
            
        Returns:
            Signal strength (0.5 - 1.0)
        """
        # Calculate percentage divergence
        divergence = abs(fast_ma - slow_ma) / slow_ma * 100
        
        # Stronger signal with larger divergence
        # Typical divergence: 0.5% - 5%
        strength = 0.5 + min(divergence / 5.0, 0.5)
        
        return min(1.0, max(0.5, strength))
    
    def get_parameters(self) -> dict[str, Any]:
        """Get strategy parameters."""
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "ma_type": self.ma_type,
        }
    
    def set_parameters(self, params: dict[str, Any]) -> None:
        """Set strategy parameters."""
        if "fast_period" in params:
            self.fast_period = params["fast_period"]
        
        if "slow_period" in params:
            self.slow_period = params["slow_period"]
        
        if "ma_type" in params:
            self.ma_type = params["ma_type"]
            # Reinitialize indicators with new type
            if self.ma_type == "ema":
                self._fast_ma = EMA(period=self.fast_period)
                self._slow_ma = EMA(period=self.slow_period)
            else:
                self._fast_ma = SMA(period=self.fast_period)
                self._slow_ma = SMA(period=self.slow_period)
        
        # Update config
        self.config.update(params)
        logger.info(f"Crossover Strategy parameters updated: {params}")
    
    def reset(self) -> None:
        """Reset strategy state."""
        self._prices.clear()
        self._prev_fast_ma = None
        self._prev_slow_ma = None
        self._last_signal = None
        self._fast_ma.reset()
        self._slow_ma.reset()
    
    def get_current_ma_values(self) -> dict[str, float | None]:
        """Get current MA values."""
        if len(self._prices) < self.slow_period:
            return {"fast_ma": None, "slow_ma": None}
        
        return {
            "fast_ma": self._fast_ma.calculate(self._prices),
            "slow_ma": self._slow_ma.calculate(self._prices),
        }
    
    def get_price_history(self) -> list[float]:
        """Get price history."""
        return self._prices.copy()
