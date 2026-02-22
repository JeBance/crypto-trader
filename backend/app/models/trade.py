"""Trade model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Trade(Base):
    """Executed trade model (fill)."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    exchange_trade_id = Column(String(100), unique=True, nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    fee_currency = Column(String(20), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    order = relationship("Order", back_populates="trades")
    
    def __repr__(self) -> str:
        return f"<Trade {self.symbol} {self.side} {self.quantity} @ {self.price}>"
    
    @property
    def total_value(self) -> float:
        """Get total trade value."""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Get net trade value after fees."""
        return self.total_value - self.fee
