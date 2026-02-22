"""Base plugin classes for the plugin system."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from app.core.types import Candle, Ticker, Order, OrderRequest, Signal, Balance, AccountInfo

if TYPE_CHECKING:
    from app.models.position import Position


class Plugin(ABC):
    """
    Abstract base class for all plugins.
    
    All plugins must inherit from this class and implement
    the initialize() and shutdown() methods.
    """
    
    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin class"
    
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the plugin.
        
        This method is called when the plugin is loaded.
        Perform any setup tasks here (API connections, etc.).
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the plugin.
        
        This method is called when the application is shutting down.
        Perform cleanup tasks here (close connections, etc.).
        """
        pass
    
    def get_info(self) -> dict[str, str]:
        """Get plugin information."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized": str(self._initialized),
        }


class ExchangePlugin(Plugin):
    """
    Abstract base class for exchange plugins.
    
    Exchange plugins provide a unified interface for interacting
    with different cryptocurrency exchanges.
    """
    
    name: str = "base_exchange"
    description: str = "Base exchange plugin"
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False, config: dict | None = None):
        super().__init__(config)
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Get ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Ticker data
        """
        pass
    
    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        """
        Get candlestick data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe (e.g., "1h", "4h", "1d")
            limit: Number of candles to retrieve
            
        Returns:
            List of candles
        """
        pass
    
    @abstractmethod
    async def create_order(self, order: OrderRequest) -> Order:
        """
        Create a new order.
        
        Args:
            order: Order request data
            
        Returns:
            Created order
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> Order:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Exchange order ID
            
        Returns:
            Cancelled order
        """
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """
        Get order status.
        
        Args:
            symbol: Trading pair symbol
            order_id: Exchange order ID
            
        Returns:
            Order data
        """
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """
        Get all open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    async def get_balance(self) -> dict[str, Balance]:
        """
        Get account balances.
        
        Returns:
            Dictionary of asset -> Balance
        """
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """
        Get full account information.
        
        Returns:
            Account info
        """
        pass


class StrategyPlugin(Plugin):
    """
    Abstract base class for strategy plugins.
    
    Strategy plugins analyze market data and generate
    trading signals.
    """
    
    name: str = "base_strategy"
    description: str = "Base strategy plugin"
    
    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self._active = False
    
    @property
    def is_active(self) -> bool:
        """Check if strategy is active."""
        return self._active
    
    def activate(self) -> None:
        """Activate the strategy."""
        self._active = True
    
    def deactivate(self) -> None:
        """Deactivate the strategy."""
        self._active = False
    
    @abstractmethod
    async def on_candle(self, candle: Candle) -> Signal | None:
        """
        Process a new candle and potentially generate a signal.
        
        Args:
            candle: New candle data
            
        Returns:
            Trading signal or None
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> dict[str, Any]:
        """
        Get strategy parameters.
        
        Returns:
            Dictionary of parameter name -> value
        """
        pass
    
    @abstractmethod
    def set_parameters(self, params: dict[str, Any]) -> None:
        """
        Set strategy parameters.
        
        Args:
            params: Dictionary of parameter name -> value
        """
        pass
    
    def get_symbols(self) -> list[str]:
        """
        Get symbols this strategy trades.
        
        Returns:
            List of symbols
        """
        return self.config.get("symbols", [])
    
    def get_timeframe(self) -> str:
        """
        Get the timeframe this strategy uses.
        
        Returns:
            Timeframe string
        """
        return self.config.get("timeframe", "1h")


class NotifierPlugin(Plugin):
    """
    Abstract base class for notifier plugins.
    
    Notifier plugins send notifications about trading events
    to various channels (Telegram, Email, etc.).
    """
    
    name: str = "base_notifier"
    description: str = "Base notifier plugin"
    
    @abstractmethod
    async def send(self, message: str, level: str = "info") -> None:
        """
        Send a notification.
        
        Args:
            message: Notification message
            level: Notification level (info, warning, error, success)
        """
        pass
    
    async def send_order_notification(self, order: Order) -> None:
        """
        Send order notification.
        
        Args:
            order: Order data
        """
        message = f"📊 Order {order.status.value.upper()}\n"
        message += f"Symbol: {order.symbol}\n"
        message += f"Side: {order.side.value}\n"
        message += f"Type: {order.type.value}\n"
        message += f"Quantity: {order.quantity}\n"
        if order.price:
            message += f"Price: {order.price}\n"
        message += f"Status: {order.status.value}"
        
        await self.send(message, level="info")

    async def send_position_notification(self, position: "Position", action: str = "opened") -> None:
        """
        Send position notification.

        Args:
            position: Position data
            action: Action type (opened, closed, updated)
        """
        emoji = {"opened": "🟢", "closed": "🔴", "updated": "🟡"}.get(action, "📊")
        message = f"{emoji} Position {action.upper()}\n"
        message += f"Symbol: {position.symbol}\n"
        message += f"Side: {position.side.value}\n"
        message += f"Quantity: {position.quantity}\n"
        message += f"Entry Price: {position.entry_price}\n"
        if position.unrealized_pnl:
            pnl_sign = "+" if position.unrealized_pnl > 0 else ""
            message += f"PnL: {pnl_sign}{position.unrealized_pnl:.2f}"
        
        await self.send(message, level="info" if action == "opened" else "success")
    
    async def send_signal_notification(self, signal: Signal) -> None:
        """
        Send signal notification.
        
        Args:
            signal: Signal data
        """
        emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(signal.action.value, "📊")
        message = f"{emoji} SIGNAL: {signal.action.value.upper()}\n"
        message += f"Symbol: {signal.symbol}\n"
        message += f"Strategy: {signal.strategy}\n"
        message += f"Strength: {signal.strength:.0%}\n"
        if signal.price:
            message += f"Price: {signal.price}"
        
        await self.send(message, level="info")
    
    async def send_error_notification(self, error: str, details: dict | None = None) -> None:
        """
        Send error notification.
        
        Args:
            error: Error message
            details: Optional error details
        """
        message = f"❌ ERROR\n{error}"
        if details:
            message += f"\nDetails: {details}"
        
        await self.send(message, level="error")
