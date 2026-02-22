"""Candle (OHLCV) model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint

from app.database import Base


class Candle(Base):
    """Candlestick (OHLCV) data model."""
    
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timeframe', 'timestamp', name='uq_candle_symbol_timeframe_timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<Candle {self.symbol} {self.timeframe} {self.timestamp}>"
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish (green)."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish (red)."""
        return self.close < self.open
    
    @property
    def body_size(self) -> float:
        """Get candle body size."""
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        """Get upper shadow size."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """Get lower shadow size."""
        return min(self.open, self.close) - self.low
