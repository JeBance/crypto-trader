"""
Backtesting Engine for testing trading strategies on historical data.

Features:
- Historical data simulation
- Order execution simulation
- Performance metrics calculation
- Trade logging
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from app.core.types import Candle, Signal, SignalAction
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.models.position import Position, PositionSide

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtesting configuration."""
    initial_capital: float = 10000.0
    commission_percent: float = 0.1  # Trading fee %
    slippage_percent: float = 0.05  # Slippage %
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class Trade:
    """Executed trade in backtest."""
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float
    pnl: float = 0.0
    trade_type: str = "entry"  # entry or exit


@dataclass
class BacktestResult:
    """Backtesting results."""
    total_return: float  # Total return %
    total_pnl: float  # Total PnL in quote currency
    win_rate: float  # Win rate %
    profit_factor: float  # Gross profit / Gross loss
    max_drawdown: float  # Maximum drawdown %
    sharpe_ratio: float  # Sharpe ratio
    total_trades: int  # Total number of trades
    winning_trades: int  # Number of winning trades
    losing_trades: int  # Number of losing trades
    avg_win: float  # Average winning trade
    avg_loss: float  # Average losing trade
    avg_trade_duration: float  # Average trade duration in candles
    final_capital: float  # Final capital
    trades: list = field(default_factory=list)  # List of trades
    equity_curve: list = field(default_factory=list)  # Equity over time
    
    def __repr__(self) -> str:
        return (
            f"BacktestResult(return={self.total_return:.2f}%, "
            f"PnL=${self.total_pnl:.2f}, "
            f"win_rate={self.win_rate:.2f}%, "
            f"trades={self.total_trades})"
        )


class BacktestEngine:
    """
    Backtesting Engine for testing strategies on historical data.
    
    Simulates trading with:
    - Realistic order execution
    - Commission and slippage
    - Position management
    - Performance metrics
    
    Example:
        >>> engine = BacktestEngine(initial_capital=10000)
        >>> result = await engine.run(strategy, candles)
        >>> print(f"Return: {result.total_return}%")
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        
        # State
        self.capital = self.config.initial_capital
        self.positions: dict[str, Position] = {}
        self.orders: list[Order] = []
        self.trades: list[Trade] = []
        self.equity_curve: list[dict] = []
        
        # Metrics tracking
        self.peak_capital = self.config.initial_capital
        self.max_drawdown = 0.0
        self.gross_profit = 0.0
        self.gross_loss = 0.0
        
        logger.info(f"BacktestEngine initialized with ${self.capital:.2f}")
    
    async def run(
        self,
        strategy,
        candles: list[Candle],
        symbol: str,
    ) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            strategy: Strategy plugin with on_candle() method
            candles: List of historical candles
            symbol: Trading pair symbol
            
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest for {symbol} with {len(candles)} candles")
        
        # Reset state
        self._reset()
        
        # Process each candle
        for i, candle in enumerate(candles):
            # Update current capital with unrealized PnL
            self._update_capital(candle)
            
            # Get signal from strategy
            signal = await strategy.on_candle(candle)
            
            if signal:
                # Process signal
                await self._process_signal(signal, candle)
            
            # Record equity
            self._record_equity(candle)
        
        # Close any open positions at the end
        await self._close_all_positions(candles[-1] if candles else None)
        
        # Calculate results
        return self._calculate_result()
    
    def _reset(self) -> None:
        """Reset backtest state."""
        self.capital = self.config.initial_capital
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
        self.equity_curve.clear()
        self.peak_capital = self.config.initial_capital
        self.max_drawdown = 0.0
        self.gross_profit = 0.0
        self.gross_loss = 0.0
    
    def _update_capital(self, candle: Candle) -> None:
        """Update capital with unrealized PnL from open positions."""
        unrealized_pnl = 0.0
        
        for position in self.positions.values():
            if position.is_open:
                position.update_pnl(candle.close)
                unrealized_pnl += position.unrealized_pnl
        
        current_capital = self.config.initial_capital + sum(t.pnl for t in self.trades) + unrealized_pnl
        
        # Track peak and drawdown
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        drawdown = (self.peak_capital - current_capital) / self.peak_capital * 100
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    async def _process_signal(self, signal: Signal, candle: Candle) -> None:
        """
        Process trading signal.
        
        Args:
            signal: Trading signal
            candle: Current candle
        """
        if signal.action == SignalAction.BUY:
            await self._open_position(signal, candle, PositionSide.LONG)
        
        elif signal.action == SignalAction.SELL:
            await self._open_position(signal, candle, PositionSide.SHORT)
        
        elif signal.action in (SignalAction.CLOSE_LONG, SignalAction.CLOSE_SHORT):
            await self._close_position(signal, candle)
    
    async def _open_position(
        self,
        signal: Signal,
        candle: Candle,
        side: PositionSide,
    ) -> None:
        """
        Open a new position.
        
        Args:
            signal: Trading signal
            candle: Current candle
            side: Position side
        """
        # Skip if position already exists
        if signal.symbol in self.positions:
            logger.debug(f"Position already exists for {signal.symbol}")
            return
        
        # Calculate position size (use 10% of capital by default)
        position_value = self.capital * 0.1
        quantity = position_value / candle.close
        
        # Apply slippage
        if side == PositionSide.LONG:
            exec_price = candle.close * (1 + self.config.slippage_percent / 100)
        else:
            exec_price = candle.close * (1 - self.config.slippage_percent / 100)
        
        # Calculate commission
        commission = (quantity * exec_price) * (self.config.commission_percent / 100)
        
        # Create position
        position = Position(
            symbol=signal.symbol,
            side=side.value,
            quantity=quantity,
            entry_price=exec_price,
            current_price=exec_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
        )
        
        self.positions[signal.symbol] = position
        
        # Record trade
        self.trades.append(Trade(
            timestamp=candle.timestamp,
            symbol=signal.symbol,
            side=side.value,
            quantity=quantity,
            price=exec_price,
            commission=commission,
            trade_type="entry",
        ))
        
        logger.info(
            f"Opened {side.value} position for {signal.symbol} @ ${exec_price:.2f}"
        )
    
    async def _close_position(self, signal: Signal, candle: Candle) -> None:
        """
        Close an existing position.
        
        Args:
            signal: Trading signal
            candle: Current candle
        """
        if signal.symbol not in self.positions:
            return
        
        position = self.positions[signal.symbol]
        
        if not position.is_open:
            return
        
        # Apply slippage
        if position.side == PositionSide.LONG.value:
            exec_price = candle.close * (1 - self.config.slippage_percent / 100)
        else:
            exec_price = candle.close * (1 + self.config.slippage_percent / 100)
        
        # Calculate PnL
        if position.side == PositionSide.LONG.value:
            pnl = (exec_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exec_price) * position.quantity
        
        # Subtract commission
        commission = (position.quantity * exec_price) * (self.config.commission_percent / 100)
        pnl -= commission * 2  # Entry + exit commission
        
        # Track gross profit/loss
        if pnl > 0:
            self.gross_profit += pnl
        else:
            self.gross_loss += abs(pnl)
        
        # Record trade
        self.trades.append(Trade(
            timestamp=candle.timestamp,
            symbol=signal.symbol,
            side=position.side,
            quantity=position.quantity,
            price=exec_price,
            commission=commission,
            pnl=pnl,
            trade_type="exit",
        ))
        
        # Close position
        position.quantity = 0
        position.closed_at = candle.timestamp
        
        logger.info(
            f"Closed {position.side} position for {signal.symbol} - "
            f"PnL: ${pnl:.2f}"
        )
    
    async def _close_all_positions(self, candle: Optional[Candle]) -> None:
        """Close all open positions."""
        if not candle:
            return
        
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            if position.is_open:
                signal = Signal(
                    action=SignalAction.CLOSE_LONG if position.side == PositionSide.LONG.value else SignalAction.CLOSE_SHORT,
                    symbol=symbol,
                    strategy="backtest",
                )
                await self._close_position(signal, candle)
    
    def _record_equity(self, candle: Candle) -> None:
        """Record equity at current candle."""
        unrealized_pnl = sum(
            p.unrealized_pnl for p in self.positions.values() if p.is_open
        )
        
        realized_pnl = sum(t.pnl for t in self.trades)
        
        total_equity = self.config.initial_capital + realized_pnl + unrealized_pnl
        
        self.equity_curve.append({
            "timestamp": candle.timestamp,
            "equity": total_equity,
            "drawdown": ((self.peak_capital - total_equity) / self.peak_capital) * 100,
        })
    
    def _calculate_result(self) -> BacktestResult:
        """Calculate backtest results."""
        # Total PnL
        total_pnl = sum(t.pnl for t in self.trades)
        total_return = (total_pnl / self.config.initial_capital) * 100
        
        # Win/Loss statistics
        winning_trades = [t for t in self.trades if t.trade_type == "exit" and t.pnl > 0]
        losing_trades = [t for t in self.trades if t.trade_type == "exit" and t.pnl < 0]
        
        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = [
                (self.equity_curve[i]["equity"] - self.equity_curve[i-1]["equity"]) / self.equity_curve[i-1]["equity"]
                for i in range(1, len(self.equity_curve))
            ]
            
            if returns:
                avg_return = sum(returns) / len(returns)
                std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Average trade duration
        # (simplified - would need entry/exit timestamps for accurate calculation)
        avg_duration = 0.0
        
        return BacktestResult(
            total_return=total_return,
            total_pnl=total_pnl,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=self.max_drawdown,
            sharpe_ratio=sharpe_ratio,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade_duration=avg_duration,
            final_capital=self.config.initial_capital + total_pnl,
            trades=self.trades,
            equity_curve=self.equity_curve,
        )
