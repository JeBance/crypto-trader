"""Order Management Service."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderExecutionError, OrderValidationError
from app.core.types import (
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
)
from app.models.order import Order as OrderModel
from app.models.position import Position as PositionModel
from app.plugins.base import ExchangePlugin
from app.core.events import EventType, publish

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Service for managing trading orders.
    
    Handles order creation, cancellation, and synchronization
    with the exchange. Publishes events for order state changes.
    
    Example:
        >>> manager = OrderManager(exchange, db_session)
        >>> order = await manager.create_market_order("BTCUSDT", "buy", 0.001)
        >>> await manager.cancel_order(order.exchange_order_id)
    """
    
    def __init__(self, exchange: ExchangePlugin, db_session: AsyncSession):
        self.exchange = exchange
        self.db = db_session
    
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        strategy_name: str | None = None,
    ) -> Order:
        """
        Create a market order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            quantity: Order quantity
            strategy_name: Optional strategy name
            
        Returns:
            Created order
            
        Raises:
            OrderValidationError: If validation fails
            OrderExecutionError: If order creation fails
        """
        # Validate
        if quantity <= 0:
            raise OrderValidationError("Quantity must be positive")
        
        order_side = OrderSide(side.lower())
        
        # Create order request
        request = OrderRequest(
            symbol=symbol,
            side=order_side,
            type=OrderType.MARKET,
            quantity=quantity,
            client_order_id=f"mkt_{datetime.utcnow().timestamp()}",
        )
        
        logger.info(f"Creating market order: {side.upper()} {quantity} {symbol}")
        
        # Execute on exchange
        try:
            order = await self.exchange.create_order(request)
            order.strategy_name = strategy_name
            
            # Save to database
            await self._save_order(order)
            
            # Publish event
            await publish(
                EventType.ORDER_CREATED,
                {
                    "order_id": order.exchange_order_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "type": "market",
                },
                source="order_manager",
            )
            
            logger.info(f"Market order created: {order.exchange_order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise OrderExecutionError(f"Failed to create order: {e}")
    
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
        strategy_name: str | None = None,
    ) -> Order:
        """
        Create a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side ('buy' or 'sell')
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            strategy_name: Optional strategy name
            
        Returns:
            Created order
            
        Raises:
            OrderValidationError: If validation fails
            OrderExecutionError: If order creation fails
        """
        # Validate
        if quantity <= 0:
            raise OrderValidationError("Quantity must be positive")
        if price <= 0:
            raise OrderValidationError("Price must be positive")
        
        order_side = OrderSide(side.lower())
        
        # Create order request
        request = OrderRequest(
            symbol=symbol,
            side=order_side,
            type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            client_order_id=f"lmt_{datetime.utcnow().timestamp()}",
        )
        
        logger.info(f"Creating limit order: {side.upper()} {quantity} {symbol} @ {price}")
        
        # Execute on exchange
        try:
            order = await self.exchange.create_order(request)
            order.strategy_name = strategy_name
            
            # Save to database
            await self._save_order(order)
            
            # Publish event
            await publish(
                EventType.ORDER_CREATED,
                {
                    "order_id": order.exchange_order_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "type": "limit",
                },
                source="order_manager",
            )
            
            logger.info(f"Limit order created: {order.exchange_order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise OrderExecutionError(f"Failed to create order: {e}")
    
    async def cancel_order(self, order_id: str) -> Order:
        """
        Cancel an existing order.
        
        Args:
            order_id: Exchange order ID
            
        Returns:
            Cancelled order
            
        Raises:
            OrderExecutionError: If cancellation fails
        """
        logger.info(f"Cancelling order: {order_id}")
        
        try:
            # Get symbol from existing order
            existing = await self.exchange.get_order("", order_id)
            symbol = existing.symbol if hasattr(existing, 'symbol') else ""
            
            order = await self.exchange.cancel_order(symbol, order_id)
            
            # Update database
            await self._update_order_status(order.exchange_order_id, order.status)
            
            # Publish event
            await publish(
                EventType.ORDER_CANCELLED,
                {
                    "order_id": order_id,
                    "symbol": symbol,
                },
                source="order_manager",
            )
            
            logger.info(f"Order cancelled: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise OrderExecutionError(f"Failed to cancel order: {e}")
    
    async def get_order(self, order_id: str) -> Order:
        """Get order by ID."""
        return await self.exchange.get_order("", order_id)
    
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """Get all open orders."""
        return await self.exchange.get_open_orders(symbol)
    
    async def sync_orders(self) -> None:
        """Synchronize orders with exchange."""
        logger.info("Synchronizing orders with exchange...")
        
        try:
            open_orders = await self.exchange.get_open_orders()
            
            for order in open_orders:
                await self._update_or_create_order(order)
            
            logger.info(f"Synchronized {len(open_orders)} orders")
            
        except Exception as e:
            logger.error(f"Failed to sync orders: {e}")
    
    async def _save_order(self, order: Order) -> None:
        """Save order to database."""
        model = OrderModel(
            exchange_order_id=order.exchange_order_id,
            symbol=order.symbol,
            side=order.side.value,
            type=order.type.value,
            quantity=order.quantity,
            price=order.price,
            filled_quantity=order.filled_quantity,
            average_price=order.average_price,
            status=order.status.value,
            strategy_name=order.strategy_name,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        
        self.db.add(model)
        await self.db.flush()
    
    async def _update_order_status(self, order_id: str, status: OrderStatus) -> None:
        """Update order status in database."""
        stmt = select(OrderModel).where(OrderModel.exchange_order_id == order_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.status = status.value
            model.updated_at = datetime.utcnow()
            
            if status == OrderStatus.FILLED:
                model.filled_at = datetime.utcnow()
            
            await self.db.flush()
    
    async def _update_or_create_order(self, order: Order) -> None:
        """Update or create order in database."""
        stmt = select(OrderModel).where(
            OrderModel.exchange_order_id == order.exchange_order_id
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.status = order.status.value
            model.filled_quantity = order.filled_quantity
            model.average_price = order.average_price
            model.updated_at = order.updated_at
        else:
            await self._save_order(order)
        
        await self.db.flush()
