"""Position Management Service."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PositionNotFoundError
from app.core.types import Order, Position, PositionSide
from app.models.position import Position as PositionModel
from app.plugins.base import ExchangePlugin
from app.core.events import EventType, publish

logger = logging.getLogger(__name__)


class PositionManager:
    """
    Service for managing trading positions.
    
    Tracks open positions, calculates PnL, and handles
    position updates. Publishes events for position changes.
    
    Example:
        >>> manager = PositionManager(exchange, db_session)
        >>> positions = await manager.get_positions()
        >>> await manager.update_pnl()
    """
    
    def __init__(self, exchange: ExchangePlugin, db_session: AsyncSession):
        self.exchange = exchange
        self.db = db_session
    
    async def get_positions(self) -> list[Position]:
        """
        Get all positions from database.
        
        Returns:
            List of positions
        """
        stmt = select(PositionModel).where(PositionModel.quantity > 0)
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_position(m) for m in models]
    
    async def get_position(self, symbol: str) -> Position | None:
        """
        Get position by symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position or None
        """
        stmt = select(PositionModel).where(PositionModel.symbol == symbol)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return self._to_position(model)
        return None
    
    async def update_pnl(self) -> None:
        """
        Update PnL for all open positions.
        
        Fetches current prices from exchange and updates
        unrealized PnL calculations.
        """
        logger.info("Updating position PnL...")
        
        positions = await self.get_positions()
        
        for position in positions:
            try:
                # Get current ticker
                ticker = await self.exchange.get_ticker(position.symbol)
                current_price = ticker.last_price
                
                # Update position
                position.update_pnl(current_price)
                
                # Update database
                await self._update_position_db(position)
                
                logger.debug(
                    f"Updated PnL for {position.symbol}: "
                    f"{position.unrealized_pnl:.2f} ({position.pnl_percent:.2f}%)"
                )
                
            except Exception as e:
                logger.error(f"Failed to update PnL for {position.symbol}: {e}")
    
    async def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> Position:
        """
        Open a new position.
        
        Args:
            symbol: Trading pair symbol
            side: Position side ('long' or 'short')
            quantity: Position quantity
            entry_price: Entry price
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            
        Returns:
            Created position
        """
        position_side = PositionSide(side.lower())
        
        position = Position(
            symbol=symbol,
            side=position_side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        # Save to database
        await self._save_position_db(position)
        
        # Publish event
        await publish(
            EventType.POSITION_OPENED,
            {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
            },
            source="position_manager",
        )
        
        logger.info(f"Position opened: {side.upper()} {quantity} {symbol} @ {entry_price}")
        return position
    
    async def close_position(self, symbol: str, close_price: float) -> Position | None:
        """
        Close a position.
        
        Args:
            symbol: Trading pair symbol
            close_price: Close price
            
        Returns:
            Closed position or None
        """
        position = await self.get_position(symbol)
        
        if not position:
            raise PositionNotFoundError(f"No open position for {symbol}")
        
        # Calculate realized PnL
        if position.side == PositionSide.LONG:
            position.realized_pnl = (close_price - position.entry_price) * position.quantity
        else:
            position.realized_pnl = (position.entry_price - close_price) * position.quantity
        
        # Update position
        position.quantity = 0
        position.closed_at = datetime.utcnow()
        
        # Update database
        await self._update_position_db(position)
        
        # Publish event
        await publish(
            EventType.POSITION_CLOSED,
            {
                "symbol": symbol,
                "side": position.side.value,
                "quantity": position.quantity,
                "realized_pnl": position.realized_pnl,
            },
            source="position_manager",
        )
        
        logger.info(
            f"Position closed: {symbol} - PnL: {position.realized_pnl:.2f}"
        )
        
        return position
    
    async def update_position_from_order(self, order: Order) -> None:
        """
        Update position based on order execution.
        
        Args:
            order: Executed order
        """
        if not order.is_filled:
            return
        
        position = await self.get_position(order.symbol)
        
        if position is None:
            # Open new position
            await self.open_position(
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.filled_quantity,
                entry_price=order.average_price,
            )
        else:
            # Update existing position
            if order.side.value == position.side.value:
                # Add to position (average entry)
                total_qty = position.quantity + order.filled_quantity
                total_value = (position.quantity * position.entry_price) + \
                             (order.filled_quantity * order.average_price)
                position.entry_price = total_value / total_qty if total_qty > 0 else 0
                position.quantity = total_qty
            else:
                # Reduce position
                position.quantity -= order.filled_quantity
                
                if position.quantity <= 0:
                    await self.close_position(order.symbol, order.average_price)
            
            await self._update_position_db(position)
    
    def _to_position(self, model: PositionModel) -> Position:
        """Convert database model to Position type."""
        return Position(
            symbol=model.symbol,
            side=PositionSide(model.side),
            quantity=model.quantity,
            entry_price=model.entry_price,
            current_price=model.current_price or model.entry_price,
            unrealized_pnl=model.unrealized_pnl or 0,
            realized_pnl=model.realized_pnl or 0,
            stop_loss=model.stop_loss,
            take_profit=model.take_profit,
            opened_at=model.opened_at,
            closed_at=model.closed_at,
        )
    
    async def _save_position_db(self, position: Position) -> None:
        """Save position to database."""
        model = PositionModel(
            symbol=position.symbol,
            side=position.side.value,
            quantity=position.quantity,
            entry_price=position.entry_price,
            current_price=position.current_price,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
        )
        
        self.db.add(model)
        await self.db.flush()
    
    async def _update_position_db(self, position: Position) -> None:
        """Update position in database."""
        stmt = select(PositionModel).where(PositionModel.symbol == position.symbol)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.quantity = position.quantity
            model.entry_price = position.entry_price
            model.current_price = position.current_price
            model.unrealized_pnl = position.unrealized_pnl
            model.realized_pnl = position.realized_pnl
            model.stop_loss = position.stop_loss
            model.take_profit = position.take_profit
            model.closed_at = position.closed_at
        else:
            await self._save_position_db(position)
        
        await self.db.flush()
