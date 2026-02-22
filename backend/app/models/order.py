"""Order model."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order(Base):
    """Order model."""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange_order_id = Column(String(100), unique=True, nullable=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    type = Column(SQLEnum(OrderType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    filled_quantity = Column(Float, default=0.0)
    average_price = Column(Float, default=0.0)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    strategy_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Order {self.symbol} {self.side.value} {self.type.value} {self.quantity}>"
    
    @property
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in (OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED)
    
    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled."""
        return self.status == OrderStatus.FILLED
    
    @property
    def fill_rate(self) -> float:
        """Get order fill rate (0.0 - 1.0)."""
        if self.quantity == 0:
            return 0.0
        return self.filled_quantity / self.quantity
