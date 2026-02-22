"""Tests for Risk Manager."""

import pytest

from app.services.risk_manager import (
    RiskManager,
    RiskConfig,
    RiskLevel,
    PositionSizeResult,
    RiskCheckResult,
)


class TestRiskConfig:
    """Tests for RiskConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RiskConfig()
        
        assert config.max_position_size_percent == 10.0
        assert config.stop_loss_percent == 2.0
        assert config.take_profit_percent == 4.0
        assert config.trailing_stop_percent == 1.0
        assert config.daily_loss_limit_percent == 5.0
        assert config.max_drawdown_percent == 15.0
        assert config.max_open_positions == 5
        assert config.risk_reward_ratio == 2.0
        assert config.max_risk_per_trade == 1.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RiskConfig(
            max_position_size_percent=20.0,
            stop_loss_percent=3.0,
            max_open_positions=10,
        )
        
        assert config.max_position_size_percent == 20.0
        assert config.stop_loss_percent == 3.0
        assert config.max_open_positions == 10


class TestPositionSizing:
    """Tests for position sizing calculations."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create RiskManager with test capital."""
        rm = RiskManager()
        rm.set_capital(10000.0)  # $10,000 capital
        return rm
    
    def test_calculate_position_size(self, risk_manager):
        """Test basic position size calculation."""
        result = risk_manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000.0,
            stop_loss_price=49000.0,  # 2% SL
        )
        
        assert isinstance(result, PositionSizeResult)
        assert result.quantity > 0
        assert result.position_value > 0
        assert result.risk_amount > 0
        assert result.stop_loss_price == 49000.0
        assert result.take_profit_price > 50000.0
    
    def test_position_size_respects_limit(self, risk_manager):
        """Test position size respects max position limit."""
        result = risk_manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000.0,
            stop_loss_price=45000.0,  # Very wide SL
        )
        
        # Position should be limited to max_position_size_percent
        max_position_value = 10000.0 * (10.0 / 100)  # 10% of $10,000
        assert result.position_value <= max_position_value
    
    def test_position_size_zero_capital(self, risk_manager):
        """Test position size with zero capital."""
        with pytest.raises(ValueError, match="Capital must be positive"):
            risk_manager.calculate_position_size(
                symbol="BTCUSDT",
                entry_price=50000.0,
                stop_loss_price=49000.0,
                capital=0,
            )
    
    def test_position_size_invalid_stop(self, risk_manager):
        """Test position size with invalid stop loss."""
        with pytest.raises(ValueError, match="Stop loss must be below entry"):
            risk_manager.calculate_position_size(
                symbol="BTCUSDT",
                entry_price=50000.0,
                stop_loss_price=51000.0,  # SL above entry
            )


class TestStopLossTakeProfit:
    """Tests for stop loss and take profit calculations."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create RiskManager."""
        return RiskManager()
    
    def test_calculate_stop_loss_long(self, risk_manager):
        """Test stop loss for long position."""
        sl = risk_manager.calculate_stop_loss(
            entry_price=100.0,
            side="long",
            percent=2.0,
        )
        
        assert sl == 98.0  # 2% below entry
    
    def test_calculate_stop_loss_short(self, risk_manager):
        """Test stop loss for short position."""
        sl = risk_manager.calculate_stop_loss(
            entry_price=100.0,
            side="short",
            percent=2.0,
        )
        
        assert sl == 102.0  # 2% above entry
    
    def test_calculate_take_profit_long(self, risk_manager):
        """Test take profit for long position."""
        tp = risk_manager.calculate_take_profit(
            entry_price=100.0,
            side="long",
            percent=4.0,
        )
        
        assert tp == 104.0  # 4% above entry
    
    def test_calculate_take_profit_short(self, risk_manager):
        """Test take profit for short position."""
        tp = risk_manager.calculate_take_profit(
            entry_price=100.0,
            side="short",
            percent=4.0,
        )
        
        assert tp == 96.0  # 4% below entry
    
    def test_calculate_trailing_stop_long(self, risk_manager):
        """Test trailing stop for long position."""
        ts = risk_manager.calculate_trailing_stop(
            highest_price=100.0,
            side="long",
            percent=1.0,
        )
        
        assert ts == 99.0  # 1% below highest


class TestRiskChecks:
    """Tests for risk checks."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create RiskManager with test capital."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        return rm
    
    def test_check_risk_valid_trade(self, risk_manager):
        """Test risk check for valid trade."""
        result = risk_manager.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert isinstance(result, RiskCheckResult)
        assert result.allowed is True
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
    
    def test_check_risk_invalid_stop_loss(self, risk_manager):
        """Test risk check with invalid stop loss."""
        result = risk_manager.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=51000.0,  # Above entry
        )
        
        assert result.allowed is False
        assert result.risk_level == RiskLevel.HIGH
        assert "Invalid stop loss" in result.message
    
    def test_check_risk_max_positions(self, risk_manager):
        """Test risk check with max positions reached."""
        # Simulate max positions
        risk_manager.open_positions_count = 5
        
        result = risk_manager.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert result.allowed is False
        assert result.risk_level == RiskLevel.HIGH
        assert "Max open positions" in result.message
    
    def test_check_risk_daily_loss_limit(self, risk_manager):
        """Test risk check with daily loss limit exceeded."""
        # Simulate daily loss
        risk_manager.daily_pnl = -600.0  # 6% of $10,000 (limit is 5%)
        
        result = risk_manager.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert result.allowed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Daily loss limit" in result.message
    
    def test_check_risk_drawdown_limit(self, risk_manager):
        """Test risk check with max drawdown exceeded."""
        # Simulate drawdown
        risk_manager.peak_capital = 12000.0
        risk_manager.total_capital = 10000.0  # 16.67% drawdown (limit is 15%)
        
        result = risk_manager.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert result.allowed is False
        assert result.risk_level == RiskLevel.CRITICAL
        assert "Max drawdown" in result.message


class TestTradeRecording:
    """Tests for trade recording."""
    
    @pytest.fixture
    def risk_manager(self):
        """Create RiskManager."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        return rm
    
    def test_record_profit_trade(self, risk_manager):
        """Test recording a profitable trade."""
        initial_capital = risk_manager.total_capital
        
        risk_manager.record_trade(
            pnl=100.0,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            exit_price=51000.0,
        )
        
        assert risk_manager.total_capital == initial_capital + 100.0
        assert risk_manager.daily_pnl == 100.0
    
    def test_record_loss_trade(self, risk_manager):
        """Test recording a losing trade."""
        initial_capital = risk_manager.total_capital
        
        risk_manager.record_trade(
            pnl=-100.0,
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            exit_price=49000.0,
        )
        
        assert risk_manager.total_capital == initial_capital - 100.0
        assert risk_manager.daily_pnl == -100.0
    
    def test_record_position_opened(self, risk_manager):
        """Test recording position opened."""
        assert risk_manager.open_positions_count == 0
        
        risk_manager.record_position_opened()
        
        assert risk_manager.open_positions_count == 1
    
    def test_reset_daily_pnl(self, risk_manager):
        """Test resetting daily PnL."""
        risk_manager.daily_pnl = 500.0
        risk_manager.reset_daily_pnl()
        
        assert risk_manager.daily_pnl == 0.0


class TestRiskManagerStatus:
    """Tests for risk manager status."""
    
    def test_get_status(self):
        """Test getting risk manager status."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        
        # Record some trades
        rm.record_trade(pnl=100.0, symbol="BTCUSDT", side="long", quantity=0.01, entry_price=50000.0, exit_price=51000.0)
        rm.record_position_opened()
        
        status = rm.get_status()
        
        assert "total_capital" in status
        assert "daily_pnl" in status
        assert "drawdown" in status
        assert "open_positions" in status
        assert "risk_level" in status
        
        assert status["total_capital"] == 10100.0
        assert status["daily_pnl"] == 100.0
        assert status["open_positions"] == 1
    
    def test_risk_level_low(self):
        """Test low risk level."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        
        status = rm.get_status()
        assert status["risk_level"] == RiskLevel.LOW.value
    
    def test_risk_level_high(self):
        """Test high risk level (near daily loss limit)."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        rm.daily_pnl = -400.0  # 4% loss (80% of 5% limit)
        
        status = rm.get_status()
        assert status["risk_level"] == RiskLevel.HIGH.value
    
    def test_risk_level_critical(self):
        """Test critical risk level (daily loss limit exceeded)."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        rm.daily_pnl = -600.0  # 6% loss (exceeds 5% limit)
        
        status = rm.get_status()
        assert status["risk_level"] == RiskLevel.CRITICAL.value
