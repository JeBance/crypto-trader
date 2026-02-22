"""Positions API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.position import Position as PositionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/positions", tags=["Positions"])


@router.get("")
async def get_positions(
    include_closed: bool = Query(False, description="Include closed positions"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all positions.
    
    - **include_closed**: Include closed positions in response
    """
    query = select(PositionModel)
    
    if not include_closed:
        query = query.where(PositionModel.quantity > 0)
    
    query = query.order_by(PositionModel.opened_at.desc())
    
    result = await db.execute(query)
    positions = result.scalars().all()
    
    return {
        "positions": [
            {
                "id": p.id,
                "symbol": p.symbol,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl,
                "realized_pnl": p.realized_pnl,
                "pnl_percent": p.pnl_percent,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "opened_at": p.opened_at.isoformat() if p.opened_at else None,
                "closed_at": p.closed_at.isoformat() if p.closed_at else None,
            }
            for p in positions
        ],
        "total": len(positions),
    }


@router.get("/{symbol}")
async def get_position(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Get a specific position by symbol.
    
    - **symbol**: Trading pair symbol (e.g., BTCUSDT)
    """
    query = select(PositionModel).where(PositionModel.symbol == symbol.upper())
    result = await db.execute(query)
    position = result.scalar_one_or_none()
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    return {
        "id": position.id,
        "symbol": position.symbol,
        "side": position.side,
        "quantity": position.quantity,
        "entry_price": position.entry_price,
        "current_price": position.current_price,
        "unrealized_pnl": position.unrealized_pnl,
        "realized_pnl": position.realized_pnl,
        "pnl_percent": position.pnl_percent,
        "stop_loss": position.stop_loss,
        "take_profit": position.take_profit,
        "opened_at": position.opened_at.isoformat() if position.opened_at else None,
        "closed_at": position.closed_at.isoformat() if position.closed_at else None,
    }


@router.post("/{symbol}/close")
async def close_position(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Close a position.
    
    - **symbol**: Trading pair symbol
    """
    # TODO: Integrate with PositionManager
    logger.info(f"Closing position: {symbol}")
    
    return {
        "status": "pending",
        "message": "Position closing is under development",
        "symbol": symbol,
    }
