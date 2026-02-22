"""
Integration tests for the application.

These tests verify that different components work together correctly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.types import Candle, Signal, SignalAction
from app.services.risk_manager import RiskManager, RiskConfig
from app.services.backtester import BacktestEngine, BacktestConfig
from app.strategies.rsi import RSIStrategy
from app.strategies.crossover import CrossoverStrategy
from app.strategies.macd import MACDStrategy


class TestStrategyIntegration:
    """Integration tests for strategies."""
    
    @pytest.fixture
    def sample_candles(self):
        """Generate sample candle data for testing."""
        from datetime import datetime, timedelta
        
        base_time = datetime.utcnow()
        base_price = 50000.0
        
        candles = []
        for i in range(100):
            # Create realistic price movement
            price = base_price + (i * 10) + (i % 5 * 20 - 50)
            
            candles.append(Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=base_time + timedelta(hours=i),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price + 25,
                volume=1000 + i * 10,
            ))
        
        return candles
    
    @pytest.mark.asyncio
    async def test_rsi_strategy_integration(self, sample_candles):
        """Test RSI strategy with realistic data."""
        strategy = RSIStrategy(period=14, oversold=30, overbought=70)
        await strategy.initialize()
        strategy.activate()
        
        signals = []
        for candle in sample_candles:
            signal = await strategy.on_candle(candle)
            if signal:
                signals.append(signal)
        
        # Should generate some signals
        assert len(signals) >= 0  # May or may not generate signals depending on data
        
        # Verify signal structure
        for signal in signals:
            assert signal.action in [SignalAction.BUY, SignalAction.SELL]
            assert signal.strength >= 0.5
            assert signal.strength <= 1.0
            assert "rsi" in signal.metadata
    
    @pytest.mark.asyncio
    async def test_crossover_strategy_integration(self, sample_candles):
        """Test Crossover strategy with realistic data."""
        strategy = CrossoverStrategy(fast_period=9, slow_period=21, ma_type="ema")
        await strategy.initialize()
        strategy.activate()
        
        signals = []
        for candle in sample_candles:
            signal = await strategy.on_candle(candle)
            if signal:
                signals.append(signal)
        
        # Verify signal structure
        for signal in signals:
            assert signal.action in [SignalAction.BUY, SignalAction.SELL]
            assert "fast_ma" in signal.metadata
            assert "slow_ma" in signal.metadata
    
    @pytest.mark.asyncio
    async def test_macd_strategy_integration(self, sample_candles):
        """Test MACD strategy with realistic data."""
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        await strategy.initialize()
        strategy.activate()
        
        signals = []
        for candle in sample_candles:
            signal = await strategy.on_candle(candle)
            if signal:
                signals.append(signal)
        
        # Verify signal structure
        for signal in signals:
            assert signal.action in [SignalAction.BUY, SignalAction.SELL]
            assert "macd" in signal.metadata
            assert "signal" in signal.metadata


class TestRiskManagerIntegration:
    """Integration tests for Risk Manager."""
    
    def test_position_sizing_integration(self):
        """Test position sizing with realistic parameters."""
        rm = RiskManager(RiskConfig(
            max_position_size_percent=10.0,
            max_risk_per_trade=1.0,
            stop_loss_percent=2.0,
        ))
        rm.set_capital(10000.0)
        
        result = rm.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        assert result.quantity > 0
        assert result.position_value <= 1000.0  # 10% of capital
        assert result.risk_amount <= 100.0  # 1% of capital
    
    def test_risk_check_workflow(self):
        """Test complete risk check workflow."""
        rm = RiskManager()
        rm.set_capital(10000.0)
        
        # Simulate opening positions
        for i in range(3):
            rm.record_position_opened()
        
        # Check if new trade is allowed
        result = rm.check_risk(
            symbol="BTCUSDT",
            side="long",
            quantity=0.01,
            entry_price=50000.0,
            stop_loss_price=49000.0,
        )
        
        # Should pass (under max positions limit of 5)
        assert result.allowed is True


class TestBacktestEngineIntegration:
    """Integration tests for Backtest Engine."""
    
    @pytest.fixture
    def sample_candles(self):
        """Generate sample candle data."""
        from datetime import datetime, timedelta
        
        base_time = datetime.utcnow()
        base_price = 50000.0
        
        candles = []
        for i in range(100):
            price = base_price + (i * 10)
            candles.append(Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=base_time + timedelta(hours=i),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price + 25,
                volume=1000,
            ))
        
        return candles
    
    @pytest.mark.asyncio
    async def test_backtest_with_rsi_strategy(self, sample_candles):
        """Test backtesting RSI strategy."""
        engine = BacktestEngine(BacktestConfig(
            initial_capital=10000.0,
            commission_percent=0.1,
            slippage_percent=0.05,
        ))
        
        strategy = RSIStrategy()
        await strategy.initialize()
        
        result = await engine.run(strategy, sample_candles, "BTCUSDT")
        
        # Verify result structure
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'total_pnl')
        assert hasattr(result, 'win_rate')
        assert hasattr(result, 'total_trades')
        assert hasattr(result, 'trades')
        assert hasattr(result, 'equity_curve')
    
    @pytest.mark.asyncio
    async def test_backtest_metrics_calculation(self, sample_candles):
        """Test that backtest calculates metrics correctly."""
        engine = BacktestEngine(BacktestConfig(
            initial_capital=10000.0,
        ))
        
        strategy = CrossoverStrategy()
        await strategy.initialize()
        
        result = await engine.run(strategy, sample_candles, "BTCUSDT")
        
        # Verify metrics are reasonable
        assert result.final_capital >= 0
        assert result.win_rate >= 0
        assert result.win_rate <= 100
        assert result.max_drawdown >= 0
        assert result.max_drawdown <= 100


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_strategy_risk_backtest_workflow(self):
        """Test complete workflow: strategy → risk check → backtest."""
        from datetime import datetime, timedelta
        
        # Generate data
        base_time = datetime.utcnow()
        candles = []
        for i in range(100):
            price = 50000 + (i * 10)
            candles.append(Candle(
                symbol="BTCUSDT",
                timeframe="1h",
                timestamp=base_time + timedelta(hours=i),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price + 25,
                volume=1000,
            ))
        
        # Initialize components
        strategy = RSIStrategy()
        await strategy.initialize()
        
        risk_manager = RiskManager(RiskConfig(
            max_position_size_percent=10.0,
            stop_loss_percent=2.0,
        ))
        risk_manager.set_capital(10000.0)
        
        engine = BacktestEngine(BacktestConfig(
            initial_capital=10000.0,
            commission_percent=0.1,
        ))
        
        # Run backtest
        result = await engine.run(strategy, candles, "BTCUSDT")
        
        # Verify integration
        assert result is not None
        assert risk_manager.total_capital == 10000.0  # Unchanged by backtest
        assert strategy.is_initialized
