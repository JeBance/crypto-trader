"""Strategy Executor for running trading strategies."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from app.core.events import EventType, publish, subscribe
from app.core.types import Candle, Signal
from app.plugins.base import StrategyPlugin, ExchangePlugin, NotifierPlugin
from app.plugins.manager import PluginManager

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Executor for running trading strategies.
    
    Manages strategy lifecycle, processes market data,
    and executes trading signals.
    
    Example:
        >>> executor = StrategyExecutor(exchange, plugin_manager)
        >>> await executor.start_strategy("rsi", symbols=["BTCUSDT"])
        >>> await executor.stop()
    """
    
    def __init__(
        self,
        exchange: ExchangePlugin,
        plugin_manager: PluginManager,
        notifier: NotifierPlugin | None = None,
    ):
        self.exchange = exchange
        self.plugin_manager = plugin_manager
        self.notifier = notifier
        
        # Active strategies: strategy_name -> {symbols, timeframe, task}
        self._active_strategies: Dict[str, dict] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """Start the strategy executor."""
        logger.info("Starting Strategy Executor...")
        self._running = True
        
        # Subscribe to candle events
        subscribe(EventType.CANDLE_CLOSED, self._on_candle_event, async_handler=True)
        
        logger.info("Strategy Executor started")
    
    async def stop(self) -> None:
        """Stop the strategy executor."""
        logger.info("Stopping Strategy Executor...")
        self._running = False
        
        # Stop all active strategies
        for strategy_name in list(self._active_strategies.keys()):
            await self.stop_strategy(strategy_name)
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        
        logger.info("Strategy Executor stopped")
    
    async def start_strategy(
        self,
        strategy_name: str,
        symbols: List[str],
        timeframe: str = "1h",
    ) -> None:
        """
        Start a strategy for specific symbols.
        
        Args:
            strategy_name: Name of the strategy plugin
            symbols: List of trading pair symbols
            timeframe: Candle timeframe
        """
        if not self.plugin_manager.has_strategy(strategy_name):
            logger.error(f"Strategy '{strategy_name}' not found")
            return
        
        strategy = self.plugin_manager.get_strategy(strategy_name)
        
        # Check if already running
        if strategy_name in self._active_strategies:
            logger.warning(f"Strategy '{strategy_name}' is already running")
            return
        
        # Activate strategy
        if hasattr(strategy, 'activate'):
            strategy.activate()
        
        # Store strategy config
        self._active_strategies[strategy_name] = {
            "strategy": strategy,
            "symbols": symbols,
            "timeframe": timeframe,
            "last_candle": {},
        }
        
        # Start data feed task
        task = asyncio.create_task(
            self._run_strategy_loop(strategy_name, symbols, timeframe)
        )
        self._tasks.append(task)
        
        # Publish event
        await publish(
            EventType.STRATEGY_STARTED,
            {
                "strategy": strategy_name,
                "symbols": symbols,
                "timeframe": timeframe,
            },
            source="strategy_executor",
        )
        
        logger.info(f"Started strategy '{strategy_name}' for {symbols}")
        
        # Notify
        if self.notifier:
            await self.notifier.send(
                f"🟢 Strategy started: {strategy_name}\n"
                f"Symbols: {', '.join(symbols)}\n"
                f"Timeframe: {timeframe}"
            )
    
    async def stop_strategy(self, strategy_name: str) -> None:
        """
        Stop a strategy.
        
        Args:
            strategy_name: Name of the strategy
        """
        if strategy_name not in self._active_strategies:
            logger.warning(f"Strategy '{strategy_name}' is not running")
            return
        
        config = self._active_strategies.pop(strategy_name)
        strategy = config["strategy"]
        
        # Deactivate strategy
        if hasattr(strategy, 'deactivate'):
            strategy.deactivate()
        
        # Reset strategy state
        if hasattr(strategy, 'reset'):
            strategy.reset()
        
        # Publish event
        await publish(
            EventType.STRATEGY_STOPPED,
            {
                "strategy": strategy_name,
            },
            source="strategy_executor",
        )
        
        logger.info(f"Stopped strategy '{strategy_name}'")
        
        # Notify
        if self.notifier:
            await self.notifier.send(
                f"🔴 Strategy stopped: {strategy_name}"
            )
    
    async def _run_strategy_loop(
        self,
        strategy_name: str,
        symbols: List[str],
        timeframe: str,
    ) -> None:
        """
        Main loop for processing candles and generating signals.
        
        Args:
            strategy_name: Strategy name
            symbols: Trading symbols
            timeframe: Candle timeframe
        """
        logger.info(f"Running strategy loop for '{strategy_name}'")
        
        while self._running and strategy_name in self._active_strategies:
            try:
                for symbol in symbols:
                    # Get candles from exchange
                    candles = await self.exchange.get_candles(
                        symbol=symbol,
                        timeframe=timeframe,
                        limit=100,
                    )
                    
                    if not candles:
                        continue
                    
                    # Get last candle
                    last_candle = candles[-1]
                    
                    # Check if we already processed this candle
                    config = self._active_strategies.get(strategy_name)
                    if config:
                        last_processed = config["last_candle"].get(symbol)
                        if last_processed and last_processed.timestamp == last_candle.timestamp:
                            continue  # Skip already processed candle
                        
                        # Store last candle timestamp
                        config["last_candle"][symbol] = last_candle
                    
                    # Process candle through strategy
                    strategy = config["strategy"]
                    signal = await strategy.on_candle(last_candle)
                    
                    if signal:
                        logger.info(
                            f"Signal generated: {signal.action.value} {symbol} "
                            f"(strength={signal.strength:.2f})"
                        )
                        
                        # Publish signal event
                        await publish(
                            EventType.SIGNAL_GENERATED,
                            {
                                "strategy": strategy_name,
                                "symbol": symbol,
                                "action": signal.action.value,
                                "strength": signal.strength,
                                "price": signal.price,
                                "stop_loss": signal.stop_loss,
                                "take_profit": signal.take_profit,
                            },
                            source="strategy_executor",
                        )
                        
                        # Notify
                        if self.notifier:
                            await self.notifier.send_signal_notification(signal)
                
                # Wait before next iteration
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                logger.info(f"Strategy loop cancelled for '{strategy_name}'")
                break
            except Exception as e:
                logger.error(f"Error in strategy loop for '{strategy_name}': {e}")
                await asyncio.sleep(5)
    
    async def _on_candle_event(self, event) -> None:
        """
        Handle candle closed event.
        
        Args:
            event: Candle event data
        """
        # Process candle through active strategies
        for strategy_name, config in self._active_strategies.items():
            if event.data.get("symbol") in config["symbols"]:
                candle = Candle(
                    symbol=event.data["symbol"],
                    timeframe=event.data.get("timeframe", "1h"),
                    timestamp=datetime.utcnow(),
                    open=event.data.get("open", 0),
                    high=event.data.get("high", 0),
                    low=event.data.get("low", 0),
                    close=event.data.get("close", 0),
                    volume=event.data.get("volume", 0),
                )
                
                strategy = config["strategy"]
                signal = await strategy.on_candle(candle)
                
                if signal:
                    await publish(
                        EventType.SIGNAL_GENERATED,
                        {
                            "strategy": strategy_name,
                            "signal": signal,
                        },
                        source="strategy_executor",
                    )
    
    def get_active_strategies(self) -> Dict[str, dict]:
        """
        Get all active strategies.
        
        Returns:
            Dictionary of active strategies
        """
        return {
            name: {
                "symbols": config["symbols"],
                "timeframe": config["timeframe"],
                "active": config["strategy"].is_active if hasattr(config["strategy"], 'is_active') else True,
            }
            for name, config in self._active_strategies.items()
        }
    
    @property
    def is_running(self) -> bool:
        """Check if executor is running."""
        return self._running
