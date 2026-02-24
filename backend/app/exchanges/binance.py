"""Binance exchange plugin."""

import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import aiohttp

from app.core.exceptions import (
    ExchangeAuthError,
    ExchangeConnectionError,
    ExchangeOrderError,
    ExchangeRateLimitError,
)
from app.core.types import (
    Balance,
    AccountInfo,
    Candle,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Ticker,
)
from app.plugins.base import ExchangePlugin

logger = logging.getLogger(__name__)


class BinanceExchange(ExchangePlugin):
    """
    Binance exchange plugin.
    
    Supports both production and testnet environments.
    Implements REST API v3 for trading operations.
    """
    
    name = "binance"
    version = "1.0.0"
    description = "Binance cryptocurrency exchange"
    
    # API Endpoints
    PROD_BASE_URL = "https://api.binance.com"
    TESTNET_BASE_URL = "https://testnet.binance.vision"
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
        config: dict | None = None,
    ):
        super().__init__(config)
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = self.TESTNET_BASE_URL if testnet else self.PROD_BASE_URL
        
        self._session: aiohttp.ClientSession | None = None
        self._recv_window = 5000
        self._last_request_time = 0
        self._request_weight = 0
    
    @property
    def is_testnet(self) -> bool:
        """Check if using testnet."""
        return self.testnet
    
    async def initialize(self) -> None:
        """Initialize exchange connection."""
        logger.info(f"Initializing Binance {'(testnet)' if self.testnet else '(production)'}...")
        
        self._session = aiohttp.ClientSession(
            headers={
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
        
        # Test connection
        try:
            await self._request("GET", "/api/v3/ping")
            logger.info("Binance connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise ExchangeConnectionError(f"Cannot connect to Binance: {e}")
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown exchange connection."""
        logger.info("Shutting down Binance connection...")
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._initialized = False
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        """
        Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            
        Returns:
            Response data
        """
        if not self._session:
            raise ExchangeConnectionError("Session not initialized")
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare parameters
        if params is None:
            params = {}
        
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self._recv_window
            query_string = urlencode(params)
            signature = hmac.new(
                self.api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            params["signature"] = signature
        
        # Make request
        try:
            async with self._session.request(
                method,
                url,
                params=params if method == "GET" else None,
                data=params if method in ("POST", "DELETE") else None,
            ) as response:
                data = await response.json()
                
                # Handle errors
                if response.status != 200:
                    error_code = data.get("code", -1)
                    error_msg = data.get("msg", "Unknown error")
                    
                    if error_code == -1003:
                        raise ExchangeRateLimitError(f"Rate limit exceeded: {error_msg}")
                    elif error_code in (-1001, -1002, -1003):
                        raise ExchangeAuthError(f"Authentication error: {error_msg}")
                    else:
                        raise ExchangeOrderError(f"API error [{error_code}]: {error_msg}")
                
                return data
                
        except aiohttp.ClientError as e:
            raise ExchangeConnectionError(f"Connection error: {e}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker data for a symbol."""
        data = await self._request("GET", "/api/v3/ticker/24hr", {"symbol": symbol})
        
        return Ticker(
            symbol=symbol,
            last_price=float(data.get("lastPrice", 0)),
            bid=float(data.get("bidPrice", 0)),
            ask=float(data.get("askPrice", 0)),
            high_24h=float(data.get("highPrice", 0)),
            low_24h=float(data.get("lowPrice", 0)),
            volume_24h=float(data.get("volume", 0)),
            change_24h=float(data.get("priceChange", 0)),
            change_percent_24h=float(data.get("priceChangePercent", 0)),
        )
    
    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        """Get candlestick data."""
        # Convert timeframe to Binance format
        tf_map = {
            "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
            "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h",
            "6h": "6h", "12h": "12h", "1d": "1d", "1w": "1w", "1M": "1M",
        }
        interval = tf_map.get(timeframe, timeframe)
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),  # Binance max is 1000
        }
        
        data = await self._request("GET", "/api/v3/klines", params)
        
        candles = []
        for candle in data:
            candles.append(Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=float(candle[5]),
            ))
        
        return candles
    
    async def create_order(self, order: OrderRequest) -> Order:
        """Create a new order."""
        params = {
            "symbol": order.symbol,
            "side": order.side.value.upper(),
            "type": order.type.value.upper(),
            "quantity": order.quantity,
        }
        
        if order.type == OrderType.LIMIT:
            params["price"] = order.price
            params["timeInForce"] = order.time_in_force
        
        if order.client_order_id:
            params["newClientOrderId"] = order.client_order_id
        
        data = await self._request("POST", "/api/v3/order", params, signed=True)
        
        return Order(
            symbol=order.symbol,
            side=order.side,
            type=order.type,
            quantity=order.quantity,
            price=order.price,
            filled_quantity=float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0) or data.get("price", 0)),
            status=self._parse_order_status(data.get("status", "")),
            exchange_order_id=str(data.get("orderId", "")),
            client_order_id=data.get("clientOrderId"),
            created_at=datetime.fromtimestamp(data.get("transactTime", 0) / 1000, tz=timezone.utc),
            strategy_name=order.strategy_name if hasattr(order, 'strategy_name') else None,
        )
    
    async def cancel_order(self, symbol: str, order_id: str) -> Order:
        """Cancel an existing order."""
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        
        data = await self._request("DELETE", "/api/v3/order", params, signed=True)
        
        return Order(
            symbol=symbol,
            side=OrderSide.BUY if data.get("side", "").lower() == "buy" else OrderSide.SELL,
            type=OrderType.MARKET,  # Simplified
            quantity=float(data.get("origQty", 0)),
            filled_quantity=float(data.get("executedQty", 0)),
            status=self._parse_order_status(data.get("status", "")),
            exchange_order_id=str(data.get("orderId", "")),
            created_at=datetime.fromtimestamp(data.get("time", 0) / 1000, tz=timezone.utc) if data.get("time") else datetime.utcnow(),
        )
    
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """Get order status."""
        params = {
            "symbol": symbol,
            "orderId": order_id,
        }
        
        data = await self._request("GET", "/api/v3/order", params, signed=True)
        
        return Order(
            symbol=symbol,
            side=OrderSide.BUY if data.get("side", "").lower() == "buy" else OrderSide.SELL,
            type=OrderType.MARKET,  # Simplified
            quantity=float(data.get("origQty", 0)),
            price=float(data.get("price", 0)),
            filled_quantity=float(data.get("executedQty", 0)),
            average_price=float(data.get("avgPrice", 0) or data.get("price", 0)),
            status=self._parse_order_status(data.get("status", "")),
            exchange_order_id=str(data.get("orderId", "")),
            client_order_id=data.get("clientOrderId"),
            created_at=datetime.fromtimestamp(data.get("time", 0) / 1000, tz=timezone.utc) if data.get("time") else datetime.utcnow(),
        )
    
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Get all open orders."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        data = await self._request("GET", "/api/v3/openOrders", params, signed=True)
        
        orders = []
        for order_data in data:
            orders.append(Order(
                symbol=order_data.get("symbol", ""),
                side=OrderSide.BUY if order_data.get("side", "").lower() == "buy" else OrderSide.SELL,
                type=OrderType.MARKET,  # Simplified
                quantity=float(order_data.get("origQty", 0)),
                price=float(order_data.get("price", 0)),
                filled_quantity=float(order_data.get("executedQty", 0)),
                status=self._parse_order_status(order_data.get("status", "")),
                exchange_order_id=str(order_data.get("orderId", "")),
                client_order_id=order_data.get("clientOrderId"),
                created_at=datetime.fromtimestamp(order_data.get("time", 0) / 1000, tz=timezone.utc) if order_data.get("time") else datetime.utcnow(),
            ))
        
        return orders
    
    async def get_balance(self) -> dict[str, Balance]:
        """Get account balances."""
        data = await self._request("GET", "/api/v3/account", signed=True)
        
        balances = {}
        for balance_data in data.get("balances", []):
            free = float(balance_data.get("free", 0))
            locked = float(balance_data.get("locked", 0))
            
            if free > 0 or locked > 0:
                asset = balance_data.get("asset", "")
                balances[asset] = Balance(
                    asset=asset,
                    free=free,
                    locked=locked,
                )
        
        return balances
    
    async def get_account_info(self) -> AccountInfo:
        """Get full account information."""
        data = await self._request("GET", "/api/v3/account", signed=True)
        
        balances = {}
        total_equity = 0.0
        
        for balance_data in data.get("balances", []):
            free = float(balance_data.get("free", 0))
            locked = float(balance_data.get("locked", 0))
            asset = balance_data.get("asset", "")
            
            if free > 0 or locked > 0:
                balances[asset] = Balance(asset=asset, free=free, locked=locked)
                # Simplified: in reality need to convert to USDT
                total_equity += free + locked
        
        return AccountInfo(
            exchange=self.name,
            balances=balances,
            total_equity=total_equity,
            total_equity_usdt=total_equity,  # Simplified
        )
    
    def _parse_order_status(self, status: str) -> OrderStatus:
        """Parse Binance order status to internal format."""
        status_map = {
            "NEW": OrderStatus.OPEN,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED,
        }
        return status_map.get(status.upper(), OrderStatus.PENDING)
