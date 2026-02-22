"""
Risk Management Service

Provides position sizing, stop-loss, take-profit calculations,
and risk limits enforcement.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskConfig:
    """Risk configuration."""
    max_position_size_percent: float = 10.0  # % of capital
    stop_loss_percent: float = 2.0  # %
    take_profit_percent: float = 4.0  # %
    trailing_stop_percent: float = 1.0  # %
    daily_loss_limit_percent: float = 5.0  # %
    max_drawdown_percent: float = 15.0  # %
    max_open_positions: int = 5
    risk_reward_ratio: float = 2.0  # Minimum R:R ratio
    max_risk_per_trade: float = 1.0  # % of capital


@dataclass
class PositionSizeResult:
    """Position sizing calculation result."""
    quantity: float
    position_value: float
    risk_amount: float  # Amount at risk (in quote currency)
    stop_loss_price: float
    take_profit_price: float
    risk_reward_ratio: float
    position_size_percent: float  # % of capital
    
    def __repr__(self) -> str:
        return (
            f"PositionSizeResult(qty={self.quantity:.6f}, "
            f"value=${self.position_value:.2f}, "
            f"risk=${self.risk_amount:.2f}, "
            f"SL={self.stop_loss_price:.2f}, "
            f"TP={self.take_profit_price:.2f})"
        )


@dataclass
class RiskCheckResult:
    """Risk check result."""
    allowed: bool
    risk_level: RiskLevel
    message: str
    details: dict
    
    def __repr__(self) -> str:
        return f"RiskCheckResult(allowed={self.allowed}, level={self.risk_level.value})"


class RiskManager:
    """
    Risk Management Service.
    
    Features:
    - Position sizing based on risk
    - Stop-loss and take-profit calculation
    - Trailing stop calculation
    - Daily loss limit tracking
    - Drawdown monitoring
    - Risk/reward ratio validation
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        
        # Tracking
        self.daily_pnl = 0.0
        self.total_capital = 0.0
        self.peak_capital = 0.0
        self.open_positions_count = 0
        
        logger.info("RiskManager initialized")
    
    def set_capital(self, capital: float) -> None:
        """
        Set total capital for risk calculations.
        
        Args:
            capital: Total capital in quote currency
        """
        self.total_capital = capital
        self.peak_capital = capital
        logger.info(f"Capital set to ${capital:.2f}")
    
    def update_capital(self, capital: float) -> None:
        """
        Update current capital and track peak.
        
        Args:
            capital: Current capital
        """
        self.total_capital = capital
        if capital > self.peak_capital:
            self.peak_capital = capital
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        capital: Optional[float] = None,
    ) -> PositionSizeResult:
        """
        Calculate position size based on risk.
        
        Uses the formula:
            Quantity = Risk Amount / (Entry Price - Stop Loss Price)
        
        Args:
            symbol: Trading pair symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            capital: Optional capital override
            
        Returns:
            PositionSizeResult with calculated values
        """
        capital = capital or self.total_capital
        
        if capital <= 0:
            raise ValueError("Capital must be positive")
        
        if entry_price <= 0:
            raise ValueError("Entry price must be positive")
        
        if stop_loss_price >= entry_price:
            raise ValueError("Stop loss must be below entry price for long positions")
        
        # Calculate risk amount (max capital to risk on this trade)
        risk_amount = capital * (self.config.max_risk_per_trade / 100)
        
        # Calculate position size based on risk
        risk_per_unit = entry_price - stop_loss_price
        quantity = risk_amount / risk_per_unit
        
        # Calculate position value
        position_value = quantity * entry_price
        
        # Check position size limit
        max_position_value = capital * (self.config.max_position_size_percent / 100)
        if position_value > max_position_value:
            # Reduce position to fit limit
            position_value = max_position_value
            quantity = position_value / entry_price
            risk_amount = quantity * risk_per_unit
        
        # Calculate take profit
        take_profit_price = entry_price * (1 + self.config.take_profit_percent / 100)
        
        # Calculate risk/reward ratio
        potential_profit = take_profit_price - entry_price
        risk_reward_ratio = potential_profit / risk_per_unit if risk_per_unit > 0 else 0
        
        # Calculate position size as % of capital
        position_size_percent = (position_value / capital) * 100
        
        return PositionSizeResult(
            quantity=quantity,
            position_value=position_value,
            risk_amount=risk_amount,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            risk_reward_ratio=risk_reward_ratio,
            position_size_percent=position_size_percent,
        )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str = "long",
        percent: Optional[float] = None,
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: Position side (long/short)
            percent: Stop loss percentage (uses config if None)
            
        Returns:
            Stop loss price
        """
        sl_percent = percent or self.config.stop_loss_percent
        
        if side.lower() == "long":
            return entry_price * (1 - sl_percent / 100)
        else:
            return entry_price * (1 + sl_percent / 100)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        side: str = "long",
        percent: Optional[float] = None,
    ) -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            side: Position side (long/short)
            percent: Take profit percentage (uses config if None)
            
        Returns:
            Take profit price
        """
        tp_percent = percent or self.config.take_profit_percent
        
        if side.lower() == "long":
            return entry_price * (1 + tp_percent / 100)
        else:
            return entry_price * (1 - tp_percent / 100)
    
    def calculate_trailing_stop(
        self,
        highest_price: float,
        side: str = "long",
        percent: Optional[float] = None,
    ) -> float:
        """
        Calculate trailing stop price.
        
        Args:
            highest_price: Highest price since entry
            side: Position side (long/short)
            percent: Trailing stop percentage (uses config if None)
            
        Returns:
            Trailing stop price
        """
        trail_percent = percent or self.config.trailing_stop_percent
        
        if side.lower() == "long":
            return highest_price * (1 - trail_percent / 100)
        else:
            return highest_price * (1 + trail_percent / 100)
    
    def check_risk(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> RiskCheckResult:
        """
        Check if a trade passes risk checks.
        
        Args:
            symbol: Trading pair symbol
            side: Position side
            quantity: Position quantity
            entry_price: Entry price
            stop_loss_price: Stop loss price
            
        Returns:
            RiskCheckResult
        """
        details = {}
        messages = []
        risk_level = RiskLevel.LOW
        
        # Check 1: Daily loss limit
        daily_loss_limit = self.total_capital * (self.config.daily_loss_limit_percent / 100)
        if self.daily_pnl < -daily_loss_limit:
            return RiskCheckResult(
                allowed=False,
                risk_level=RiskLevel.CRITICAL,
                message="Daily loss limit exceeded",
                details={
                    "daily_pnl": self.daily_pnl,
                    "limit": -daily_loss_limit,
                },
            )
        
        # Check 2: Max open positions
        if self.open_positions_count >= self.config.max_open_positions:
            return RiskCheckResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                message=f"Max open positions limit reached ({self.config.max_open_positions})",
                details={"open_positions": self.open_positions_count},
            )
        
        # Check 3: Position size limit
        position_value = quantity * entry_price
        max_position_value = self.total_capital * (self.config.max_position_size_percent / 100)
        
        if position_value > max_position_value:
            messages.append(f"Position size exceeds limit ({position_value:.2f} > {max_position_value:.2f})")
            risk_level = RiskLevel.MEDIUM
        
        # Check 4: Risk/Reward ratio
        take_profit_price = self.calculate_take_profit(entry_price, side)
        if side.lower() == "long":
            risk = entry_price - stop_loss_price
            reward = take_profit_price - entry_price
        else:
            risk = stop_loss_price - entry_price
            reward = entry_price - take_profit_price
        
        if risk > 0:
            rr_ratio = reward / risk
            if rr_ratio < self.config.risk_reward_ratio:
                messages.append(
                    f"Risk/Reward ratio too low ({rr_ratio:.2f} < {self.config.risk_reward_ratio})"
                )
                risk_level = RiskLevel.MEDIUM
            
            details["risk_reward_ratio"] = rr_ratio
        
        # Check 5: Drawdown limit
        current_drawdown = ((self.peak_capital - self.total_capital) / self.peak_capital) * 100
        if current_drawdown > self.config.max_drawdown_percent:
            return RiskCheckResult(
                allowed=False,
                risk_level=RiskLevel.CRITICAL,
                message=f"Max drawdown exceeded ({current_drawdown:.2f}% > {self.config.max_drawdown_percent}%)",
                details={"drawdown": current_drawdown},
            )
        
        # Check 6: Stop loss validity
        if side.lower() == "long" and stop_loss_price >= entry_price:
            return RiskCheckResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                message="Invalid stop loss (must be below entry for long)",
                details={"stop_loss": stop_loss_price, "entry": entry_price},
            )
        
        if side.lower() == "short" and stop_loss_price <= entry_price:
            return RiskCheckResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                message="Invalid stop loss (must be above entry for short)",
                details={"stop_loss": stop_loss_price, "entry": entry_price},
            )
        
        # All checks passed
        allowed = risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        
        return RiskCheckResult(
            allowed=allowed,
            risk_level=risk_level,
            message="; ".join(messages) if messages else "Risk check passed",
            details=details,
        )
    
    def record_trade(
        self,
        pnl: float,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        exit_price: float,
    ) -> None:
        """
        Record a completed trade.
        
        Args:
            pnl: Profit/Loss from the trade
            symbol: Trading pair symbol
            side: Position side
            quantity: Position quantity
            entry_price: Entry price
            exit_price: Exit price
        """
        self.daily_pnl += pnl
        self.open_positions_count = max(0, self.open_positions_count - 1)
        
        # Update capital
        self.update_capital(self.total_capital + pnl)
        
        logger.info(
            f"Trade recorded: {symbol} {side} - PnL: ${pnl:.2f}, "
            f"Daily PnL: ${self.daily_pnl:.2f}"
        )
    
    def record_position_opened(self) -> None:
        """Record a new position opened."""
        self.open_positions_count += 1
        logger.debug(f"Position opened, count: {self.open_positions_count}")
    
    def reset_daily_pnl(self) -> None:
        """Reset daily PnL (call at start of each trading day)."""
        logger.info(f"Resetting daily PnL: ${self.daily_pnl:.2f}")
        self.daily_pnl = 0.0
    
    def get_status(self) -> dict:
        """Get risk manager status."""
        drawdown = ((self.peak_capital - self.total_capital) / self.peak_capital) * 100 if self.peak_capital > 0 else 0
        
        return {
            "total_capital": self.total_capital,
            "peak_capital": self.peak_capital,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_percent": (self.daily_pnl / self.total_capital) * 100 if self.total_capital > 0 else 0,
            "drawdown": drawdown,
            "drawdown_percent": drawdown,
            "open_positions": self.open_positions_count,
            "max_positions": self.config.max_open_positions,
            "risk_level": self._calculate_current_risk_level().value,
        }
    
    def _calculate_current_risk_level(self) -> RiskLevel:
        """Calculate current overall risk level."""
        # Check daily loss
        daily_loss_limit = self.config.daily_loss_limit_percent
        current_daily_loss = abs(min(0, self.daily_pnl)) / self.total_capital * 100
        
        if current_daily_loss >= daily_loss_limit:
            return RiskLevel.CRITICAL
        
        if current_daily_loss >= daily_loss_limit * 0.8:
            return RiskLevel.HIGH
        
        if current_daily_loss >= daily_loss_limit * 0.5:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
