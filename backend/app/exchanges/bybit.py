"""Bybit exchange plugin."""

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


class BybitExchange(ExchangePlugin):
    """
    Bybit exchange plugin.
    
    Supports both production and testnet environments.
    Implements V5 API for trading operations.
    """
    
    name = "bybit"
    version = "1.0.0"
    description = "Bybit cryptocurrency exchange"
    
    # API Endpoints
    PROD_BASE_URL = "https://api.bybit.com"
    TESTNET_BASE_URL = "https://api-testnet.bybit.com"
    
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
    
    @property
    def is_testnet(self) -> bool:
        """Check if using testnet."""
        return self.testnet
    
    async def initialize(self) -> None:
        """Initialize exchange connection."""
        logger.info(f"Initializing Bybit {'(testnet)' if self.testnet else '(production)'}...")
        
        self._session = aiohttp.ClientSession(
            headers={
                "X-BAPI-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=aiohttp.ClientTimeout(total=30),
        )
        
        # Test connection
        try:
            await self._request("GET", "/v5/market/time")
            logger.info("Bybit connection successful")
        except Exception as e:
            logger.error(f"Failed to connect to Bybit: {e}")
            raise ExchangeConnectionError(f"Cannot connect to Bybit: {e}")
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown exchange connection."""
        logger.info("Shutting down Bybit connection...")
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._initialized = False
    
    def _generate_signature(self, params: str) -> str:
        """Generate HMAC SHA256 signature."""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            params.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> dict[str, Any]:
        """
        Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            body: Request body
            
        Returns:
            Response data
        """
        if not self._session:
            raise ExchangeConnectionError("Session not initialized")
        
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": str(int(time.time() * 1000)),
            "X-BAPI-RECV-WINDOW": str(self._recv_window),
        }
        
        # Generate signature for signed endpoints
        if body or (method != "GET" and params):
            query_string = ""
            if params:
                query_string = urlencode(params)
            body_string = ""
            if body:
                body_string = str(body).replace("'", '"')
            
            sign_params = headers["X-BAPI-TIMESTAMP"] + self.api_key + str(self._recv_window) + query_string + body_string
            headers["X-BAPI-SIGN"] = self._generate_signature(sign_params)
        
        # Make request
        try:
            async with self._session.request(
                method,
                url,
                params=params if method == "GET" else None,
                json=body if method in ("POST", "DELETE") else None,
                headers=headers,
            ) as response:
                data = await response.json()
                
                # Handle errors
                if data.get("retCode", 0) != 0:
                    error_code = data.get("retCode", -1)
                    error_msg = data.get("retMsg", "Unknown error")
                    
                    if error_code in (10001, 10002, 10003):
                        raise ExchangeAuthError(f"Authentication error: {error_msg}")
                    elif error_code in (10004, 10005, 10006):
                        raise ExchangeRateLimitError(f"Rate limit exceeded: {error_msg}")
                    else:
                        raise ExchangeOrderError(f"API error [{error_code}]: {error_msg}")
                
                return data.get("result", {})
                
        except aiohttp.ClientError as e:
            raise ExchangeConnectionError(f"Connection error: {e}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker data for a symbol."""
        params = {"category": "spot", "symbol": symbol}
        data = await self._request("GET", "/v5/market/tickers", params)
        
        ticker_data = data.get("list", [{}])[0]
        
        return Ticker(
            symbol=symbol,
            last_price=float(ticker_data.get("lastPrice", 0)),
            bid=float(ticker_data.get("bid1Price", 0)),
            ask=float(ticker_data.get("ask1Price", 0)),
            high_24h=float(ticker_data.get("highPrice24h", 0)),
            low_24h=float(ticker_data.get("lowPrice24h", 0)),
            volume_24h=float(ticker_data.get("volume24h", 0)),
            change_24h=float(ticker_data.get("price24hPcnt", 0)),
            change_percent_24h=float(ticker_data.get("price24hPcnt", 0)) * 100,
        )
    
    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        """Get candlestick data."""
        # Convert timeframe to Bybit format
        tf_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15",
            "30m": "30", "1h": "60", "2h": "120", "4h": "240",
            "6h": "360", "12h": "720", "1d": "D", "1w": "W", "1M": "M",
        }
        interval = tf_map.get(timeframe, timeframe)
        
        params = {
            "category": "spot",
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),
        }
        
        data = await self._request("GET", "/v5/market/kline", params)
        
        candles = []
        for candle in data.get("list", []):
            candles.append(Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.fromtimestamp(int(candle[0]) / 1000, tz=timezone.utc),
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=float(candle[5]),
            ))
        
        # Reverse to get chronological order
        candles.reverse()
        return candles
    
    async def create_order(self, order: OrderRequest) -> Order:
        """Create a new order."""
        body = {
            "category": "spot",
            "symbol": order.symbol,
            "side": order.side.value.upper(),
            "orderType": order.type.value.upper(),
            "qty": str(order.quantity),
        }
        
        if order.type == OrderType.LIMIT and order.price:
            body["price"] = str(order.price)
        
        if order.client_order_id:
            body["orderLinkId"] = order.client_order_id
        
        data = await self._request("POST", "/v5/order/create", body=body)
        
        return Order(
            symbol=order.symbol,
            side=order.side,
            type=order.type,
            quantity=order.quantity,
            price=order.price,
            status=OrderStatus.OPEN,
            exchange_order_id=data.get("orderId", ""),
            client_order_id=data.get("orderLinkId"),
            strategy_name=getattr(order, 'strategy_name', None),
        )
    
    async def cancel_order(self, symbol: str, order_id: str) -> Order:
        """Cancel an existing order."""
        body = {
            "category": "spot",
            "symbol": symbol,
            "orderId": order_id,
        }
        
        await self._request("POST", "/v5/order/cancel", body=body)
        
        return Order(
            symbol=symbol,
            side=OrderSide.BUY,  # Unknown, simplified
            type=OrderType.MARKET,
            quantity=0,
            status=OrderStatus.CANCELLED,
            exchange_order_id=order_id,
        )
    
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """Get order status."""
        params = {
            "category": "spot",
            "symbol": symbol,
            "orderId": order_id,
        }
        
        data = await self._request("GET", "/v5/order/realtime", params)
        order_data = data.get("list", [{}])[0]
        
        return Order(
            symbol=symbol,
            side=OrderSide.BUY if order_data.get("side", "").lower() == "buy" else OrderSide.SELL,
            type=OrderType.MARKET,  # Simplified
            quantity=float(order_data.get("qty", 0)),
            price=float(order_data.get("price", 0)),
            filled_quantity=float(order_data.get("cumExecQty", 0)),
            status=self._parse_order_status(order_data.get("orderStatus", "")),
            exchange_order_id=order_data.get("orderId", ""),
            client_order_id=order_data.get("orderLinkId"),
        )
    
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Get all open orders."""
        params = {"category": "spot"}
        if symbol:
            params["symbol"] = symbol
        
        data = await self._request("GET", "/v5/order/realtime", params)
        
        orders = []
        for order_data in data.get("list", []):
            orders.append(Order(
                symbol=order_data.get("symbol", ""),
                side=OrderSide.BUY if order_data.get("side", "").lower() == "buy" else OrderSide.SELL,
                type=OrderType.MARKET,  # Simplified
                quantity=float(order_data.get("qty", 0)),
                price=float(order_data.get("price", 0)),
                filled_quantity=float(order_data.get("cumExecQty", 0)),
                status=self._parse_order_status(order_data.get("orderStatus", "")),
                exchange_order_id=order_data.get("orderId", ""),
                client_order_id=order_data.get("orderLinkId"),
            ))
        
        return orders
    
    async def get_balance(self) -> dict[str, Balance]:
        """Get account balances."""
        params = {"accountType": "SPOT"}
        data = await self._request("GET", "/v5/account/wallet-balance", params)
        
        balances = {}
        for coin_data in data.get("coin", []):
            available = float(coin_data.get("availableToWithdraw", 0))
            locked = float(coin_data.get("locked", 0))
            asset = coin_data.get("coin", "")
            
            if available > 0 or locked > 0:
                balances[asset] = Balance(
                    asset=asset,
                    free=available,
                    locked=locked,
                )
        
        return balances
    
    async def get_account_info(self) -> AccountInfo:
        """Get full account information."""
        params = {"accountType": "SPOT"}
        data = await self._request("GET", "/v5/account/wallet-balance", params)
        
        balances = {}
        total_equity = float(data.get("totalEquity", 0))
        
        for coin_data in data.get("coin", []):
            available = float(coin_data.get("availableToWithdraw", 0))
            locked = float(coin_data.get("locked", 0))
            asset = coin_data.get("coin", "")
            
            if available > 0 or locked > 0:
                balances[asset] = Balance(asset=asset, free=available, locked=locked)
        
        return AccountInfo(
            exchange=self.name,
            balances=balances,
            total_equity=total_equity,
            total_equity_usdt=total_equity,
        )
    
    def _parse_order_status(self, status: str) -> OrderStatus:
        """Parse Bybit order status to internal format."""
        status_map = {
            "New": OrderStatus.OPEN,
            "PartiallyFilled": OrderStatus.PARTIALLY_FILLED,
            "Filled": OrderStatus.FILLED,
            "Cancelled": OrderStatus.CANCELLED,
            "Rejected": OrderStatus.REJECTED,
        }
        return status_map.get(status, OrderStatus.PENDING)
