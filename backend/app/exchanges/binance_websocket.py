"""Binance WebSocket Stream Client for real-time market data."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from app.core.types import Candle, Ticker, Trade
from app.core.events import publish, EventType

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """
    Binance WebSocket client for real-time market data streams.
    
    Supports:
    - Kline/Candlestick streams
    - 24hr Ticker streams
    - Trade streams
    - Order book streams
    
    Usage:
        >>> ws_client = BinanceWebSocketClient()
        >>> await ws_client.connect()
        >>> await ws_client.subscribe_kline("btcusdt", "1h")
        >>> await ws_client.subscribe_ticker("btcusdt")
        >>> # Receive real-time updates
        >>> await ws_client.disconnect()
    """
    
    # WebSocket endpoints
    WS_STREAM_URL = "wss://stream.binance.com:9443/ws"
    WS_TESTNET_URL = "wss://testnet.binance.vision/ws"
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.ws_url = self.WS_TESTNET_URL if testnet else self.WS_STREAM_URL
        
        # Connection state
        self._ws: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_delay = 5
        self._max_reconnect_attempts = 10
        
        # Subscriptions
        self._subscriptions: Dict[str, dict] = {}  # stream_name -> config
        
        # Callbacks
        self._on_kline: Optional[Callable] = None
        self._on_ticker: Optional[Callable] = None
        self._on_trade: Optional[Callable] = None
        
        # Statistics
        self._stats = {
            "messages_received": 0,
            "klines_received": 0,
            "tickers_received": 0,
            "trades_received": 0,
            "reconnects": 0,
            "last_message_time": None,
        }
    
    async def connect(self) -> bool:
        """
        Connect to Binance WebSocket.
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Connecting to Binance WebSocket ({'testnet' if self.testnet else 'production'})...")
            
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            
            self._connected = True
            self._running = True
            
            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info("Binance WebSocket connected")
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Binance WebSocket."""
        self._running = False
        
        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._connected = False
        self._subscriptions.clear()
        
        logger.info("Binance WebSocket disconnected")
    
    async def _receive_loop(self) -> None:
        """Main loop for receiving WebSocket messages."""
        reconnect_attempts = 0
        
        while self._running:
            try:
                if not self._ws or not self._connected:
                    # Try to reconnect
                    if reconnect_attempts < self._max_reconnect_attempts:
                        logger.info(f"Reconnecting to WebSocket (attempt {reconnect_attempts + 1})...")
                        await asyncio.sleep(self._reconnect_delay)
                        success = await self.connect()
                        if success:
                            reconnect_attempts = 0
                            # Resubscribe
                            await self._resubscribe_all()
                        else:
                            reconnect_attempts += 1
                    else:
                        logger.error("Max reconnect attempts reached")
                        break
                
                # Receive message
                message = await self._ws.recv()
                self._stats["messages_received"] += 1
                self._stats["last_message_time"] = datetime.now(timezone.utc)
                
                # Process message
                await self._process_message(json.loads(message))
                
            except websockets.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                self._connected = False
                reconnect_attempts += 1
                self._stats["reconnects"] += 1
            
            except asyncio.CancelledError:
                logger.info("WebSocket receive loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in WebSocket receive loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, data: dict) -> None:
        """
        Process incoming WebSocket message.
        
        Args:
            data: Parsed JSON message
        """
        try:
            # Kline/Candlestick
            if 'k' in data:
                await self._handle_kline(data)
            
            # 24hr Ticker
            elif '24hrTicker' in data or ('e' in data and data['e'] == '24hrTicker'):
                await self._handle_ticker(data)
            
            # Trade
            elif 'a' in data and 'p' in data:  # Simple trade format
                await self._handle_trade(data)
            
            # Combined stream
            elif 'stream' in data and 'data' in data:
                await self._process_message(data['data'])
            
            else:
                logger.debug(f"Unknown message type: {data}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_kline(self, data: dict) -> None:
        """
        Handle kline/candlestick message.
        
        Args:
            data: Kline message data
        """
        k = data['k']
        
        candle = Candle(
            symbol=k['s'].upper(),
            timeframe=self._interval_to_timeframe(k['k']),
            timestamp=datetime.fromtimestamp(k['t'] / 1000, tz=timezone.utc),
            open=float(k['o']),
            high=float(k['h']),
            low=float(k['l']),
            close=float(k['c']),
            volume=float(k['v']),
        )
        
        self._stats["klines_received"] += 1
        
        # Call callback
        if self._on_kline:
            await self._on_kline(candle, k['x'])  # k['x'] = is closed
        
        # Publish event
        if k['x']:  # Only publish on candle close
            await publish(
                EventType.CANDLE_CLOSED,
                {
                    "symbol": candle.symbol,
                    "timeframe": candle.timeframe,
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                },
                source="websocket",
            )
    
    async def _handle_ticker(self, data: dict) -> None:
        """
        Handle 24hr ticker message.
        
        Args:
            data: Ticker message data
        """
        ticker = Ticker(
            symbol=data.get('s', data.get('symbol', '')).upper(),
            last_price=float(data.get('c', data.get('lastPrice', 0))),
            bid=float(data.get('b', data.get('bidPrice', 0))),
            ask=float(data.get('a', data.get('askPrice', 0))),
            high_24h=float(data.get('h', data.get('highPrice', 0))),
            low_24h=float(data.get('l', data.get('lowPrice', 0))),
            volume_24h=float(data.get('v', data.get('volume', 0))),
            change_24h=float(data.get('p', data.get('priceChange', 0))),
            change_percent_24h=float(data.get('P', data.get('priceChangePercent', 0))),
        )
        
        self._stats["tickers_received"] += 1
        
        # Call callback
        if self._on_ticker:
            await self._on_ticker(ticker)
    
    async def _handle_trade(self, data: dict) -> None:
        """
        Handle trade message.
        
        Args:
            data: Trade message data
        """
        trade = Trade(
            symbol=data.get('s', '').upper(),
            side='buy' if data.get('m', False) else 'sell',  # m = is buyer maker
            price=float(data.get('p', 0)),
            quantity=float(data.get('q', 0)),
            trade_id=str(data.get('t', data.get('a', ''))),
            timestamp=datetime.fromtimestamp(data.get('T', 0) / 1000, tz=timezone.utc),
        )
        
        self._stats["trades_received"] += 1
        
        # Call callback
        if self._on_trade:
            await self._on_trade(trade)
    
    async def subscribe_kline(self, symbol: str, timeframe: str) -> bool:
        """
        Subscribe to kline/candlestick stream.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
        
        Returns:
            True if subscribed successfully
        """
        symbol_lower = symbol.lower()
        interval = self._timeframe_to_interval(timeframe)
        stream_name = f"{symbol_lower}@kline_{interval}"
        
        return await self._subscribe(stream_name, {
            "type": "kline",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "interval": interval,
        })
    
    async def subscribe_ticker(self, symbol: str) -> bool:
        """
        Subscribe to 24hr ticker stream.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            True if subscribed successfully
        """
        symbol_lower = symbol.lower()
        stream_name = f"{symbol_lower}@ticker"
        
        return await self._subscribe(stream_name, {
            "type": "ticker",
            "symbol": symbol.upper(),
        })
    
    async def subscribe_trade(self, symbol: str) -> bool:
        """
        Subscribe to trade stream.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            True if subscribed successfully
        """
        symbol_lower = symbol.lower()
        stream_name = f"{symbol_lower}@trade"
        
        return await self._subscribe(stream_name, {
            "type": "trade",
            "symbol": symbol.upper(),
        })
    
    async def unsubscribe(self, stream_name: str) -> bool:
        """
        Unsubscribe from a stream.
        
        Args:
            stream_name: Stream name (e.g., "btcusdt@kline_1h")
        
        Returns:
            True if unsubscribed successfully
        """
        if not self._connected or not self._ws:
            return False
        
        try:
            message = {
                "method": "UNSUBSCRIBE",
                "params": [stream_name],
                "id": id(stream_name),
            }
            
            await self._ws.send(json.dumps(message))
            
            self._subscriptions.pop(stream_name, None)
            
            logger.debug(f"Unsubscribed from {stream_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {stream_name}: {e}")
            return False
    
    async def _subscribe(self, stream_name: str, config: dict) -> bool:
        """
        Subscribe to a WebSocket stream.
        
        Args:
            stream_name: Stream name
            config: Stream configuration
        
        Returns:
            True if subscribed successfully
        """
        if not self._connected or not self._ws:
            logger.warning("Cannot subscribe: not connected")
            return False
        
        try:
            message = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": id(stream_name),
            }
            
            await self._ws.send(json.dumps(message))
            
            # Wait for response
            response = await asyncio.wait_for(self._ws.recv(), timeout=5)
            resp_data = json.loads(response)
            
            if 'error' in resp_data:
                logger.error(f"Subscription error for {stream_name}: {resp_data['error']}")
                return False
            
            self._subscriptions[stream_name] = config
            
            logger.debug(f"Subscribed to {stream_name}")
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"Subscription timeout for {stream_name}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to subscribe to {stream_name}: {e}")
            return False
    
    async def _resubscribe_all(self) -> None:
        """Resubscribe to all streams after reconnect."""
        logger.info(f"Resubscribing to {len(self._subscriptions)} streams...")
        
        for stream_name, config in self._subscriptions.items():
            try:
                await self._subscribe(stream_name, config)
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to resubscribe to {stream_name}: {e}")
    
    def _timeframe_to_interval(self, timeframe: str) -> str:
        """Convert timeframe to Binance interval format."""
        tf_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h",
            "6h": "6h", "12h": "12h", "1d": "1d", "1w": "1w", "1M": "1M",
        }
        return tf_map.get(timeframe, timeframe)
    
    def _interval_to_timeframe(self, interval: str) -> str:
        """Convert Binance interval to timeframe format."""
        return interval  # Same format
    
    def set_kline_callback(self, callback: Callable) -> None:
        """
        Set callback for kline updates.
        
        Args:
            callback: Async function(candle, is_closed)
        """
        self._on_kline = callback
    
    def set_ticker_callback(self, callback: Callable) -> None:
        """
        Set callback for ticker updates.
        
        Args:
            callback: Async function(ticker)
        """
        self._on_ticker = callback
    
    def set_trade_callback(self, callback: Callable) -> None:
        """
        Set callback for trade updates.
        
        Args:
            callback: Async function(trade)
        """
        self._on_trade = callback
    
    def get_stats(self) -> dict:
        """Get WebSocket statistics."""
        return {
            "connected": self._connected,
            "subscriptions": len(self._subscriptions),
            "subscription_list": list(self._subscriptions.keys()),
            **self._stats,
        }
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._ws is not None
