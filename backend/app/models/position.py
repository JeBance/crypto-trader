"""Position model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime

from app.database import Base


class Position(Base):
    """Trading position model."""
    
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(Float, nullable=False, default=0.0)
    entry_price = Column(Float, nullable=False, default=0.0)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Position {self.symbol} {self.side} {self.quantity}>"
    
    @property
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.quantity > 0
    
    @property
    def position_value(self) -> float:
        """Get current position value."""
        return self.quantity * (self.current_price or self.entry_price)
    
    @property
    def pnl_percent(self) -> float:
        """Get PnL as percentage."""
        if self.entry_price == 0:
            return 0.0
        if self.side == "long":
            return ((self.current_price or self.entry_price) - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - (self.current_price or self.entry_price)) / self.entry_price * 100
    
    def update_pnl(self, current_price: float) -> None:
        """Update unrealized PnL based on current price."""
        self.current_price = current_price
        if self.side == "long":
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
