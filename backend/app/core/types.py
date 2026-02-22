"""Core types and data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Timeframe(str, Enum):
    """Candlestick timeframes."""
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H12 = "12h"
    D1 = "1d"
    W1 = "1w"
    M1 = "1M"


class OrderSide(str, Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(str, Enum):
    """Position side."""
    LONG = "long"
    SHORT = "short"


class SignalAction(str, Enum):
    """Trading signal action."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"


@dataclass
class Candle:
    """Candlestick (OHLCV) data."""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish."""
        return self.close < self.open
    
    @property
    def body_size(self) -> float:
        """Get candle body size."""
        return abs(self.close - self.open)
    
    @property
    def range_size(self) -> float:
        """Get candle range (high - low)."""
        return self.high - self.low


@dataclass
class Ticker:
    """Ticker data (24h stats)."""
    symbol: str
    last_price: float
    bid: float = 0.0
    ask: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    change_percent_24h: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrderRequest:
    """Order request data."""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    client_order_id: str | None = None
    
    def __post_init__(self):
        if self.type == OrderType.LIMIT and self.price is None:
            raise ValueError("LIMIT order requires price")
        if self.type in (OrderType.STOP_LOSS, OrderType.STOP_LIMIT) and self.stop_price is None:
            raise ValueError("STOP order requires stop_price")


@dataclass
class Order:
    """Order data."""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    filled_quantity: float = 0.0
    average_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    exchange_order_id: str | None = None
    client_order_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: datetime | None = None
    strategy_name: str | None = None
    
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
        """Get fill rate (0.0 - 1.0)."""
        if self.quantity == 0:
            return 0.0
        return self.filled_quantity / self.quantity


@dataclass
class Position:
    """Trading position data."""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    opened_at: datetime = field(default_factory=datetime.utcnow)
    closed_at: datetime | None = None
    
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
        if self.side == PositionSide.LONG:
            return ((self.current_price or self.entry_price) - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - (self.current_price or self.entry_price)) / self.entry_price * 100
    
    def update_pnl(self, current_price: float) -> None:
        """Update unrealized PnL."""
        self.current_price = current_price
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity


@dataclass
class Signal:
    """Trading signal from strategy."""
    action: SignalAction
    symbol: str
    strategy: str
    strength: float = 1.0  # 0.0 - 1.0
    price: float = 0.0
    stop_loss: float | None = None
    take_profit: float | None = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Signal strength must be between 0.0 and 1.0")


@dataclass
class Balance:
    """Account balance for an asset."""
    asset: str
    free: float = 0.0
    locked: float = 0.0
    
    @property
    def total(self) -> float:
        """Get total balance."""
        return self.free + self.locked
    
    @property
    def available(self) -> float:
        """Get available (free) balance."""
        return self.free


@dataclass
class AccountInfo:
    """Account information."""
    exchange: str
    balances: dict[str, Balance] = field(default_factory=dict)
    total_equity: float = 0.0
    total_equity_usdt: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Trade:
    """Executed trade (fill)."""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    fee: float = 0.0
    fee_currency: str | None = None
    order_id: str | None = None
    trade_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def total_value(self) -> float:
        """Get total trade value."""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Get net value after fees."""
        return self.total_value - self.fee
