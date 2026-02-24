"""Market data models for historical data storage."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
    JSON,
)

from app.database import Base


class MonitoredPair(Base):
    """
    Trading pair monitored by user.
    
    Stores user's selected pairs for data collection.
    Data is NEVER deleted automatically when monitoring stops.
    """
    
    __tablename__ = "monitored_pairs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)  # 'binance', 'bybit', etc.
    symbol = Column(String(20), nullable=False)  # 'BTCUSDT', 'ETHUSDT', etc.
    
    # Monitoring configuration
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    timeframes = Column(String(255), default="1h,4h,1d")  # Comma-separated timeframes
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_data_at = Column(DateTime, nullable=True)  # Last successful data fetch
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Additional metadata
    
    __table_args__ = (
        UniqueConstraint('exchange', 'symbol', name='uq_monitored_pair_exchange_symbol'),
        Index('idx_monitored_pair_active', 'is_active'),
        Index('idx_monitored_pair_exchange', 'exchange'),
    )
    
    def __repr__(self) -> str:
        return f"<MonitoredPair {self.exchange}:{self.symbol} (active={self.is_active})>"


class Candle(Base):
    """
    Candlestick (OHLCV) historical data.
    
    Stores all available candle data for monitored pairs.
    Data is NEVER deleted automatically.
    """
    
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)  # 'binance', 'bybit', etc.
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    
    # Candle data
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)
    
    # Additional data
    quote_volume = Column(Float, default=0.0)  # Volume in quote currency
    trades_count = Column(Integer, default=0)  # Number of trades
    taker_buy_volume = Column(Float, default=0.0)  # Taker buy base volume
    taker_buy_quote_volume = Column(Float, default=0.0)  # Taker buy quote volume
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        UniqueConstraint('exchange', 'symbol', 'timeframe', 'timestamp', name='uq_candle_exchange_symbol_timeframe_timestamp'),
        Index('idx_candle_symbol_timeframe', 'symbol', 'timeframe'),
        Index('idx_candle_exchange_timestamp', 'exchange', 'timestamp'),
        Index('idx_candle_full', 'exchange', 'symbol', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<Candle {self.exchange}:{self.symbol} {self.timeframe} {self.timestamp}>"
    
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
    def range_size(self) -> float:
        """Get candle range (high - low)."""
        return self.high - self.low
    
    @property
    def upper_shadow(self) -> float:
        """Get upper shadow size."""
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        """Get lower shadow size."""
        return min(self.open, self.close) - self.low


class Ticker(Base):
    """
    24-hour ticker statistics.
    
    Stores periodic snapshots of ticker data.
    """
    
    __tablename__ = "tickers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Ticker data
    timestamp = Column(DateTime, nullable=False, index=True)
    last_price = Column(Float, nullable=False)
    bid_price = Column(Float, default=0.0)
    ask_price = Column(Float, default=0.0)
    high_24h = Column(Float, default=0.0)
    low_24h = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    quote_volume_24h = Column(Float, default=0.0)
    change_24h = Column(Float, default=0.0)
    change_percent_24h = Column(Float, default=0.0)
    trades_count_24h = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_ticker_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_ticker_timestamp', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<Ticker {self.exchange}:{self.symbol} @ {self.last_price}>"


class Trade(Base):
    """
    Individual trade (transaction) data.
    
    Stores recent trades from the exchange.
    """
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Trade data
    trade_id = Column(String(50), nullable=True, index=True)  # Exchange trade ID
    order_id = Column(String(50), nullable=True, index=True)  # Related order ID
    timestamp = Column(DateTime, nullable=False, index=True)
    
    side = Column(String(10), nullable=False)  # 'buy' or 'sell'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    quote_quantity = Column(Float, nullable=True)  # Price * Quantity
    
    # Fee data (if available)
    fee = Column(Float, default=0.0)
    fee_currency = Column(String(20), nullable=True)
    fee_in_usdt = Column(Float, default=0.0)
    
    # Maker/taker indicator
    is_maker = Column(Integer, default=0)  # 1 = maker, 0 = taker
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint('exchange', 'trade_id', name='uq_trade_exchange_trade_id'),
        Index('idx_trade_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_trade_exchange_timestamp', 'exchange', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<Trade {self.exchange}:{self.symbol} {self.side} {self.quantity}@{self.price}>"
    
    @property
    def total_value(self) -> float:
        """Get total trade value."""
        return self.quantity * self.price
    
    @property
    def net_value(self) -> float:
        """Get net value after fees."""
        return self.total_value - (self.fee_in_usdt or 0)


class OrderBookSnapshot(Base):
    """
    Order book snapshot.
    
    Stores periodic snapshots of the order book.
    Useful for liquidity analysis.
    """
    
    __tablename__ = "order_book_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Order book data (stored as JSON for flexibility)
    bids = Column(JSON, nullable=False)  # [[price, quantity], ...]
    asks = Column(JSON, nullable=False)  # [[price, quantity], ...]
    
    # Summary statistics
    best_bid = Column(Float, nullable=False)
    best_ask = Column(Float, nullable=False)
    spread = Column(Float, nullable=False)
    spread_percent = Column(Float, nullable=False)
    bid_depth = Column(Float, default=0.0)  # Total bid volume
    ask_depth = Column(Float, default=0.0)  # Total ask volume
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_orderbook_exchange_symbol', 'exchange', 'symbol'),
        Index('idx_orderbook_timestamp', 'timestamp'),
    )
    
    def __repr__(self) -> str:
        return f"<OrderBookSnapshot {self.exchange}:{self.symbol} spread={self.spread}>"


class DataCollectionLog(Base):
    """
    Log of data collection activities.
    
    Tracks when data was collected for each pair/timeframe.
    """
    
    __tablename__ = "data_collection_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=True)  # None for tickers/trades
    
    # Collection type
    data_type = Column(String(20), nullable=False)  # 'candle', 'ticker', 'trade', 'orderbook'
    
    # Result
    status = Column(String(20), nullable=False)  # 'success', 'error', 'partial'
    records_collected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Time range of collected data
    data_from = Column(DateTime, nullable=True)
    data_to = Column(DateTime, nullable=True)
    
    # Timestamps
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        Index('idx_collection_log_exchange', 'exchange'),
        Index('idx_collection_log_symbol', 'symbol'),
        Index('idx_collection_log_collected_at', 'collected_at'),
    )
    
    def __repr__(self) -> str:
        return f"<DataCollectionLog {self.exchange}:{self.symbol} {self.data_type} {self.status}>"
