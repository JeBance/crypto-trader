"""Orders API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.types import OrderSide, OrderType
from app.database import get_db
from app.models.order import Order as OrderModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("")
async def get_orders(
    status: str = Query(None, description="Filter by status"),
    symbol: str = Query(None, description="Filter by symbol"),
    limit: int = Query(50, ge=1, le=500, description="Number of orders to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all orders with optional filtering.
    
    - **status**: Filter by order status (pending, open, filled, cancelled)
    - **symbol**: Filter by trading pair symbol
    - **limit**: Maximum number of orders to return (1-500)
    """
    query = select(OrderModel)
    
    if status:
        query = query.where(OrderModel.status == status.lower())
    
    if symbol:
        query = query.where(OrderModel.symbol == symbol.upper())
    
    query = query.order_by(OrderModel.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return {
        "orders": [
            {
                "id": o.id,
                "exchange_order_id": o.exchange_order_id,
                "symbol": o.symbol,
                "side": o.side,
                "type": o.type,
                "quantity": o.quantity,
                "price": o.price,
                "filled_quantity": o.filled_quantity,
                "average_price": o.average_price,
                "status": o.status,
                "strategy_name": o.strategy_name,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in orders
        ],
        "total": len(orders),
    }


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific order by ID.
    
    - **order_id**: Exchange order ID
    """
    query = select(OrderModel).where(OrderModel.exchange_order_id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": order.id,
        "exchange_order_id": order.exchange_order_id,
        "symbol": order.symbol,
        "side": order.side,
        "type": order.type,
        "quantity": order.quantity,
        "price": order.price,
        "filled_quantity": order.filled_quantity,
        "average_price": order.average_price,
        "status": order.status,
        "strategy_name": order.strategy_name,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


@router.post("")
async def create_order(
    symbol: str,
    side: str,
    type: str,
    quantity: float,
    price: float = None,
    strategy_name: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order.
    
    - **symbol**: Trading pair symbol (e.g., BTCUSDT)
    - **side**: Order side (buy, sell)
    - **type**: Order type (market, limit)
    - **quantity**: Order quantity
    - **price**: Limit price (required for limit orders)
    - **strategy_name**: Optional strategy name
    """
    # TODO: Integrate with OrderManager and Exchange
    # For now, return a placeholder response
    
    logger.info(f"Creating order: {side} {quantity} {symbol} (type={type})")
    
    return {
        "status": "pending",
        "message": "Order creation is under development",
        "order": {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
            "price": price,
            "strategy_name": strategy_name,
        },
    }


@router.delete("/{order_id}")
async def cancel_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Cancel an existing order.
    
    - **order_id**: Exchange order ID
    """
    # TODO: Integrate with OrderManager and Exchange
    
    logger.info(f"Cancelling order: {order_id}")
    
    return {
        "status": "success",
        "message": "Order cancellation is under development",
        "order_id": order_id,
    }
