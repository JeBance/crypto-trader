"""Bybit WebSocket Stream Client for real-time market data."""

import asyncio
import json
import logging
import time
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from app.core.types import Candle, Ticker, Trade
from app.core.events import publish, EventType

logger = logging.getLogger(__name__)


class BybitWebSocketClient:
    """
    Bybit WebSocket client for real-time market data streams.
    
    Supports:
    - Kline/Candlestick streams
    - 24hr Ticker streams
    - Trade streams
    
    Usage:
        >>> ws_client = BybitWebSocketClient()
        >>> await ws_client.connect()
        >>> await ws_client.subscribe_kline("BTCUSDT", "60")
        >>> await ws_client.subscribe_ticker("BTCUSDT")
        >>> await ws_client.disconnect()
    """
    
    # WebSocket endpoints
    WS_SPOT_URL = "wss://stream.bybit.com/v5/public/spot"
    WS_TESTNET_URL = "wss://stream-testnet.bybit.com/v5/public/spot"
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.ws_url = self.WS_TESTNET_URL if testnet else self.WS_SPOT_URL
        
        # Connection state
        self._ws: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_delay = 5
        self._max_reconnect_attempts = 10
        
        # Subscriptions
        self._subscriptions: Dict[str, dict] = {}
        
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
        """Connect to Bybit WebSocket."""
        try:
            logger.info(f"Connecting to Bybit WebSocket ({'testnet' if self.testnet else 'production'})...")
            
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
            
            logger.info("Bybit WebSocket connected")
            return True
        
        except Exception as e:
            logger.error(f"Failed to connect to Bybit WebSocket: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Bybit WebSocket."""
        self._running = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._connected = False
        self._subscriptions.clear()
        
        logger.info("Bybit WebSocket disconnected")
    
    async def _receive_loop(self) -> None:
        """Main loop for receiving WebSocket messages."""
        reconnect_attempts = 0
        
        while self._running:
            try:
                if not self._ws or not self._connected:
                    if reconnect_attempts < self._max_reconnect_attempts:
                        logger.info(f"Reconnecting to WebSocket (attempt {reconnect_attempts + 1})...")
                        await asyncio.sleep(self._reconnect_delay)
                        success = await self.connect()
                        if success:
                            reconnect_attempts = 0
                            await self._resubscribe_all()
                        else:
                            reconnect_attempts += 1
                    else:
                        logger.error("Max reconnect attempts reached")
                        break
                
                message = await self._ws.recv()
                self._stats["messages_received"] += 1
                self._stats["last_message_time"] = datetime.now(timezone.utc)
                
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
        """Process incoming WebSocket message."""
        try:
            # Check message type
            if 'topic' in data:
                topic = data['topic']
                
                # Kline
                if topic.startswith('kline'):
                    await self._handle_kline(data)
                
                # Ticker
                elif topic.startswith('tickers'):
                    await self._handle_ticker(data)
                
                # Trade
                elif topic.startswith('publicTrade'):
                    await self._handle_trade(data)
            
            # Ping/pong
            elif 'op' in data and data['op'] == 'pong':
                logger.debug("Received pong response")
            
            # Subscription response
            elif 'op' in data and data['op'] in ('subscribe', 'unsubscribe'):
                logger.debug(f"Subscription response: {data}")
            
            else:
                logger.debug(f"Unknown message type: {data}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_kline(self, data: dict) -> None:
        """Handle kline message."""
        try:
            candle_data = data['data'][0]
            
            candle = Candle(
                symbol=candle_data['symbol'],
                timeframe=self._interval_to_timeframe(candle_data['interval']),
                timestamp=datetime.fromtimestamp(int(candle_data['start']) / 1000, tz=timezone.utc),
                open=float(candle_data['open']),
                high=float(candle_data['high']),
                low=float(candle_data['low']),
                close=float(candle_data['close']),
                volume=float(candle_data['volume']),
            )
            
            self._stats["klines_received"] += 1
            
            is_closed = candle_data['confirm']
            
            if self._on_kline:
                await self._on_kline(candle, is_closed)
            
            # Publish event on candle close
            if is_closed:
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
        
        except Exception as e:
            logger.error(f"Error handling kline: {e}")
    
    async def _handle_ticker(self, data: dict) -> None:
        """Handle ticker message."""
        try:
            ticker_data = data['data'][0]
            
            ticker = Ticker(
                symbol=ticker_data['symbol'],
                last_price=float(ticker_data['lastPrice']),
                bid=float(ticker_data['bid1Price']),
                ask=float(ticker_data['ask1Price']),
                high_24h=float(ticker_data['highPrice24h']),
                low_24h=float(ticker_data['lowPrice24h']),
                volume_24h=float(ticker_data['volume24h']),
                change_24h=float(ticker_data['price24hPcnt']),
                change_percent_24h=float(ticker_data['price24hPcnt']) * 100,
            )
            
            self._stats["tickers_received"] += 1
            
            if self._on_ticker:
                await self._on_ticker(ticker)
        
        except Exception as e:
            logger.error(f"Error handling ticker: {e}")
    
    async def _handle_trade(self, data: dict) -> None:
        """Handle trade message."""
        try:
            for trade_data in data['data']:
                trade = Trade(
                    symbol=trade_data['symbol'],
                    side='sell' if trade_data['side'] == 'Sell' else 'buy',
                    price=float(trade_data['price']),
                    quantity=float(trade_data['size']),
                    trade_id=str(trade_data['execId']),
                    timestamp=datetime.fromtimestamp(int(trade_data['T']) / 1000, tz=timezone.utc),
                )
                
                self._stats["trades_received"] += 1
                
                if self._on_trade:
                    await self._on_trade(trade)
        
        except Exception as e:
            logger.error(f"Error handling trade: {e}")
    
    async def subscribe_kline(self, symbol: str, timeframe: str) -> bool:
        """
        Subscribe to kline stream.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
        """
        interval = self._timeframe_to_interval(timeframe)
        topic = f"kline.{interval}.{symbol}"
        
        return await self._subscribe(topic, {
            "type": "kline",
            "symbol": symbol,
            "timeframe": timeframe,
            "interval": interval,
        })
    
    async def subscribe_ticker(self, symbol: str) -> bool:
        """Subscribe to 24hr ticker stream."""
        topic = f"tickers.{symbol}"
        
        return await self._subscribe(topic, {
            "type": "ticker",
            "symbol": symbol,
        })
    
    async def subscribe_trade(self, symbol: str) -> bool:
        """Subscribe to trade stream."""
        topic = f"publicTrade.{symbol}"
        
        return await self._subscribe(topic, {
            "type": "trade",
            "symbol": symbol,
        })
    
    async def _subscribe(self, topic: str, config: dict) -> bool:
        """Subscribe to a topic."""
        if not self._connected or not self._ws:
            logger.warning("Cannot subscribe: not connected")
            return False
        
        try:
            message = {
                "op": "subscribe",
                "args": [topic],
            }
            
            await self._ws.send(json.dumps(message))
            
            # Wait for response
            response = await asyncio.wait_for(self._ws.recv(), timeout=10)
            resp_data = json.loads(response)
            
            if resp_data.get('op') == 'subscribe' and resp_data.get('retCode') == 0:
                self._subscriptions[topic] = config
                logger.debug(f"Subscribed to {topic}")
                return True
            else:
                logger.error(f"Subscription error for {topic}: {resp_data}")
                return False
        
        except asyncio.TimeoutError:
            logger.warning(f"Subscription timeout for {topic}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            return False
    
    async def _resubscribe_all(self) -> None:
        """Resubscribe to all topics after reconnect."""
        logger.info(f"Resubscribing to {len(self._subscriptions)} topics...")
        
        for topic, config in self._subscriptions.items():
            try:
                await self._subscribe(topic, config)
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Failed to resubscribe to {topic}: {e}")
    
    def _timeframe_to_interval(self, timeframe: str) -> str:
        """Convert timeframe to Bybit interval format."""
        tf_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15",
            "30m": "30", "1h": "60", "2h": "120", "4h": "240",
            "6h": "360", "12h": "720", "1d": "D", "1w": "W", "1M": "M",
        }
        return tf_map.get(timeframe, timeframe)
    
    def _interval_to_timeframe(self, interval: str) -> str:
        """Convert Bybit interval to timeframe format."""
        reverse_map = {
            "1": "1m", "3": "3m", "5": "5m", "15": "15m",
            "30": "30m", "60": "1h", "120": "2h", "240": "4h",
            "360": "6h", "720": "12h", "D": "1d", "W": "1w", "M": "1M",
        }
        return reverse_map.get(interval, interval)
    
    def set_kline_callback(self, callback: Callable) -> None:
        """Set callback for kline updates."""
        self._on_kline = callback
    
    def set_ticker_callback(self, callback: Callable) -> None:
        """Set callback for ticker updates."""
        self._on_ticker = callback
    
    def set_trade_callback(self, callback: Callable) -> None:
        """Set callback for trade updates."""
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
