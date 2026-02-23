"""WebSocket Stream Manager - Manages real-time WebSocket connections."""

import asyncio
import logging
from typing import Dict, List, Optional, Callable

from app.core.types import Candle, Ticker, Trade
from app.exchanges.binance_websocket import BinanceWebSocketClient
from app.exchanges.bybit_websocket import BybitWebSocketClient

logger = logging.getLogger(__name__)


class WebSocketStreamManager:
    """
    Manager for real-time WebSocket streams from multiple exchanges.
    
    Features:
    - Multi-exchange support (Binance, Bybit)
    - Automatic reconnection
    - Stream subscription management
    - Real-time data callbacks
    - Statistics and monitoring
    
    Usage:
        >>> manager = WebSocketStreamManager()
        >>> await manager.start()
        >>> await manager.subscribe_kline("binance", "BTCUSDT", "1h")
        >>> await manager.subscribe_ticker("bybit", "BTCUSDT")
        >>> stats = manager.get_stats()
        >>> await manager.stop()
    """
    
    def __init__(self):
        # WebSocket clients
        self._binance_ws: Optional[BinanceWebSocketClient] = None
        self._bybit_ws: Optional[BybitWebSocketClient] = None
        
        # State
        self._running = False
        self._subscriptions: Dict[str, Dict] = {}  # "exchange:symbol:type" -> config
        
        # Callbacks
        self._on_candle_callbacks: List[Callable] = []
        self._on_ticker_callbacks: List[Callable] = []
        self._on_trade_callbacks: List[Callable] = []
        
        # Statistics
        self._stats = {
            "candles_received": 0,
            "tickers_received": 0,
            "trades_received": 0,
            "start_time": None,
        }
    
    async def start(self) -> None:
        """Start WebSocket stream manager."""
        if self._running:
            logger.warning("WebSocketStreamManager is already running")
            return
        
        logger.info("Starting WebSocket Stream Manager...")
        self._running = True
        self._stats["start_time"] = asyncio.get_event_loop().time()
        
        # Initialize clients
        self._binance_ws = BinanceWebSocketClient(testnet=True)
        self._bybit_ws = BybitWebSocketClient(testnet=True)
        
        # Set callbacks
        self._binance_ws.set_kline_callback(self._on_binance_kline)
        self._binance_ws.set_ticker_callback(self._on_binance_ticker)
        self._binance_ws.set_trade_callback(self._on_binance_trade)
        
        self._bybit_ws.set_kline_callback(self._on_bybit_kline)
        self._bybit_ws.set_ticker_callback(self._on_bybit_ticker)
        self._bybit_ws.set_trade_callback(self._on_bybit_trade)
        
        # Connect clients
        await self._connect_clients()
        
        logger.info("WebSocket Stream Manager started")
    
    async def stop(self) -> None:
        """Stop WebSocket stream manager."""
        if not self._running:
            return
        
        logger.info("Stopping WebSocket Stream Manager...")
        self._running = False
        
        # Disconnect clients
        if self._binance_ws:
            await self._binance_ws.disconnect()
        
        if self._bybit_ws:
            await self._bybit_ws.disconnect()
        
        self._subscriptions.clear()
        
        logger.info("WebSocket Stream Manager stopped")
    
    async def _connect_clients(self) -> None:
        """Connect all WebSocket clients."""
        # Connect Binance
        try:
            await self._binance_ws.connect()
            logger.info("Binance WebSocket connected")
        except Exception as e:
            logger.error(f"Failed to connect Binance WebSocket: {e}")
        
        # Connect Bybit
        try:
            await self._bybit_ws.connect()
            logger.info("Bybit WebSocket connected")
        except Exception as e:
            logger.error(f"Failed to connect Bybit WebSocket: {e}")
    
    async def subscribe_kline(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
    ) -> bool:
        """
        Subscribe to kline/candlestick stream.
        
        Args:
            exchange: Exchange name ("binance" or "bybit")
            symbol: Trading pair symbol
            timeframe: Candle timeframe
        
        Returns:
            True if subscribed successfully
        """
        key = f"{exchange}:{symbol}:kline:{timeframe}"
        
        if key in self._subscriptions:
            logger.warning(f"Already subscribed to {key}")
            return True
        
        success = False
        
        if exchange.lower() == "binance":
            if self._binance_ws and self._binance_ws.is_connected:
                success = await self._binance_ws.subscribe_kline(symbol, timeframe)
        
        elif exchange.lower() == "bybit":
            if self._bybit_ws and self._bybit_ws.is_connected:
                success = await self._bybit_ws.subscribe_kline(symbol, timeframe)
        
        if success:
            self._subscriptions[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "type": "kline",
                "timeframe": timeframe,
            }
            logger.info(f"Subscribed to {exchange} kline: {symbol} {timeframe}")
        
        return success
    
    async def subscribe_ticker(
        self,
        exchange: str,
        symbol: str,
    ) -> bool:
        """
        Subscribe to ticker stream.
        
        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
        
        Returns:
            True if subscribed successfully
        """
        key = f"{exchange}:{symbol}:ticker"
        
        if key in self._subscriptions:
            logger.warning(f"Already subscribed to {key}")
            return True
        
        success = False
        
        if exchange.lower() == "binance":
            if self._binance_ws and self._binance_ws.is_connected:
                success = await self._binance_ws.subscribe_ticker(symbol)
        
        elif exchange.lower() == "bybit":
            if self._bybit_ws and self._bybit_ws.is_connected:
                success = await self._bybit_ws.subscribe_ticker(symbol)
        
        if success:
            self._subscriptions[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "type": "ticker",
            }
            logger.info(f"Subscribed to {exchange} ticker: {symbol}")
        
        return success
    
    async def subscribe_trade(
        self,
        exchange: str,
        symbol: str,
    ) -> bool:
        """
        Subscribe to trade stream.
        
        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
        
        Returns:
            True if subscribed successfully
        """
        key = f"{exchange}:{symbol}:trade"
        
        if key in self._subscriptions:
            logger.warning(f"Already subscribed to {key}")
            return True
        
        success = False
        
        if exchange.lower() == "binance":
            if self._binance_ws and self._binance_ws.is_connected:
                success = await self._binance_ws.subscribe_trade(symbol)
        
        elif exchange.lower() == "bybit":
            if self._bybit_ws and self._bybit_ws.is_connected:
                success = await self._bybit_ws.subscribe_trade(symbol)
        
        if success:
            self._subscriptions[key] = {
                "exchange": exchange,
                "symbol": symbol,
                "type": "trade",
            }
            logger.info(f"Subscribed to {exchange} trade: {symbol}")
        
        return success
    
    async def unsubscribe(self, key: str) -> bool:
        """
        Unsubscribe from a stream.
        
        Args:
            key: Subscription key (exchange:symbol:type[:timeframe])
        
        Returns:
            True if unsubscribed successfully
        """
        if key not in self._subscriptions:
            logger.warning(f"Not subscribed to {key}")
            return False
        
        config = self._subscriptions.pop(key)
        exchange = config["exchange"]
        symbol = config["symbol"]
        stream_type = config["type"]
        
        # Build stream name
        if stream_type == "kline":
            timeframe = config.get("timeframe", "1h")
            # Unsubscribe logic here
        
        logger.info(f"Unsubscribed from {key}")
        return True
    
    # Binance callbacks
    async def _on_binance_kline(self, candle: Candle, is_closed: bool) -> None:
        """Handle Binance kline update."""
        if is_closed:
            self._stats["candles_received"] += 1
            
            for callback in self._on_candle_callbacks:
                try:
                    await callback(candle, "binance")
                except Exception as e:
                    logger.error(f"Error in candle callback: {e}")
    
    async def _on_binance_ticker(self, ticker: Ticker) -> None:
        """Handle Binance ticker update."""
        self._stats["tickers_received"] += 1
        
        for callback in self._on_ticker_callbacks:
            try:
                await callback(ticker, "binance")
            except Exception as e:
                logger.error(f"Error in ticker callback: {e}")
    
    async def _on_binance_trade(self, trade: Trade) -> None:
        """Handle Binance trade update."""
        self._stats["trades_received"] += 1
        
        for callback in self._on_trade_callbacks:
            try:
                await callback(trade, "binance")
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")
    
    # Bybit callbacks
    async def _on_bybit_kline(self, candle: Candle, is_closed: bool) -> None:
        """Handle Bybit kline update."""
        if is_closed:
            self._stats["candles_received"] += 1
            
            for callback in self._on_candle_callbacks:
                try:
                    await callback(candle, "bybit")
                except Exception as e:
                    logger.error(f"Error in candle callback: {e}")
    
    async def _on_bybit_ticker(self, ticker: Ticker) -> None:
        """Handle Bybit ticker update."""
        self._stats["tickers_received"] += 1
        
        for callback in self._on_ticker_callbacks:
            try:
                await callback(ticker, "bybit")
            except Exception as e:
                logger.error(f"Error in ticker callback: {e}")
    
    async def _on_bybit_trade(self, trade: Trade) -> None:
        """Handle Bybit trade update."""
        self._stats["trades_received"] += 1
        
        for callback in self._on_trade_callbacks:
            try:
                await callback(trade, "bybit")
            except Exception as e:
                logger.error(f"Error in trade callback: {e}")
    
    def add_candle_callback(self, callback: Callable) -> None:
        """
        Add callback for candle updates.
        
        Args:
            callback: Async function(candle, exchange)
        """
        self._on_candle_callbacks.append(callback)
    
    def add_ticker_callback(self, callback: Callable) -> None:
        """
        Add callback for ticker updates.
        
        Args:
            callback: Async function(ticker, exchange)
        """
        self._on_ticker_callbacks.append(callback)
    
    def add_trade_callback(self, callback: Callable) -> None:
        """
        Add callback for trade updates.
        
        Args:
            callback: Async function(trade, exchange)
        """
        self._on_trade_callbacks.append(callback)
    
    def get_stats(self) -> dict:
        """Get stream manager statistics."""
        uptime = 0
        if self._stats["start_time"]:
            uptime = asyncio.get_event_loop().time() - self._stats["start_time"]
        
        return {
            "running": self._running,
            "subscriptions": len(self._subscriptions),
            "subscription_list": list(self._subscriptions.keys()),
            "binance_connected": self._binance_ws.is_connected if self._binance_ws else False,
            "bybit_connected": self._bybit_ws.is_connected if self._bybit_ws else False,
            "candles_received": self._stats["candles_received"],
            "tickers_received": self._stats["tickers_received"],
            "trades_received": self._stats["trades_received"],
            "uptime_seconds": uptime,
        }
    
    def get_subscriptions(self) -> Dict[str, Dict]:
        """Get all active subscriptions."""
        return self._subscriptions.copy()
    
    @property
    def is_running(self) -> bool:
        """Check if manager is running."""
        return self._running
