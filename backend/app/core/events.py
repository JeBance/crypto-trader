"""Event Bus for loose coupling between components."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """System event types."""
    
    # Order events
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    
    # Position events
    POSITION_OPENED = "position_opened"
    POSITION_UPDATED = "position_updated"
    POSITION_CLOSED = "position_closed"
    
    # Strategy events
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"
    SIGNAL_GENERATED = "signal_generated"
    
    # Market events
    PRICE_UPDATED = "price_updated"
    CANDLE_CLOSED = "candle_closed"
    
    # Account events
    BALANCE_UPDATED = "balance_updated"
    
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    ERROR_OCCURRED = "error_occurred"
    
    # Notification events
    NOTIFICATION_SENT = "notification_sent"


@dataclass
class Event:
    """
    Event data structure.
    
    Attributes:
        type: Event type
        data: Event payload
        timestamp: Event timestamp
        source: Event source (component name)
    """
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    
    def __repr__(self) -> str:
        return f"Event(type={self.type.value}, data={self.data})"


EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event, Any], Any]


class EventBus:
    """
    Central event bus for pub/sub messaging between components.
    
    Provides loose coupling between system components through
    event-driven architecture.
    
    Example:
        ```python
        # Subscribe to events
        bus.subscribe(EventType.ORDER_FILLED, my_handler)
        
        # Publish event
        await bus.publish(EventType.ORDER_FILLED, {"order_id": "123"})
        
        # Unsubscribe
        bus.unsubscribe(EventType.ORDER_FILLED, my_handler)
        ```
    """
    
    _instance: "EventBus | None" = None
    
    def __new__(cls) -> "EventBus":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._handlers: dict[EventType, list[Callable]] = defaultdict(list)
        self._async_handlers: dict[EventType, list[Callable]] = defaultdict(list)
        self._event_history: list[Event] = []
        self._max_history = 100
        self._lock = asyncio.Lock()
        self._initialized = True
        
        logger.info("EventBus initialized")
    
    @classmethod
    def get_instance(cls) -> "EventBus":
        """Get the singleton instance."""
        return cls()
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
    
    def subscribe(self, event_type: EventType, handler: Callable, async_handler: bool = False) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle the event
            async_handler: Whether the handler is async
        """
        if async_handler:
            self._async_handlers[event_type].append(handler)
            logger.debug(f"Subscribed async handler to {event_type.value}")
        else:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed handler to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler from {event_type.value}")
        
        if handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed async handler from {event_type.value}")
    
    def unsubscribe_all(self, event_type: EventType) -> None:
        """
        Unsubscribe all handlers from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
        """
        self._handlers[event_type].clear()
        self._async_handlers[event_type].clear()
        logger.debug(f"Unsubscribed all handlers from {event_type.value}")
    
    async def publish(self, event_type: EventType, data: dict[str, Any] = None, source: str = "") -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event
            data: Event payload data
            source: Event source component name
        """
        event = Event(
            type=event_type,
            data=data or {},
            source=source,
        )
        
        # Store in history
        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        logger.debug(f"Publishing event: {event}")
        
        # Call sync handlers
        for handler in self._handlers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in sync handler for {event_type.value}: {e}")
        
        # Call async handlers
        if self._async_handlers[event_type]:
            results = await asyncio.gather(
                *[self._call_async_handler(handler, event) for handler in self._async_handlers[event_type]],
                return_exceptions=True,
            )
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error in async handler for {event_type.value}: {result}")
    
    async def _call_async_handler(self, handler: Callable, event: Event) -> None:
        """Call an async handler safely."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Error in async handler: {e}")
            raise
    
    def publish_sync(self, event_type: EventType, data: dict[str, Any] = None, source: str = "") -> None:
        """
        Publish a synchronous event.
        
        Note: This only calls synchronous handlers.
        
        Args:
            event_type: Type of event
            data: Event payload data
            source: Event source component name
        """
        event = Event(
            type=event_type,
            data=data or {},
            source=source,
        )
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        logger.debug(f"Publishing sync event: {event}")
        
        # Call sync handlers only
        for handler in self._handlers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in sync handler for {event_type.value}: {e}")
    
    def get_history(self, event_type: EventType | None = None, limit: int = 50) -> list[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type is None:
            return self._event_history[-limit:]
        
        return [e for e in self._event_history if e.type == event_type][-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")
    
    def get_stats(self) -> dict:
        """
        Get event bus statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_handlers": sum(len(h) for h in self._handlers.values()) + 
                            sum(len(h) for h in self._async_handlers.values()),
            "sync_handlers": sum(len(h) for h in self._handlers.values()),
            "async_handlers": sum(len(h) for h in self._async_handlers.values()),
            "event_types_subscribed": len([t for t in self._handlers if self._handlers[t]]) +
                                     len([t for t in self._async_handlers if self._async_handlers[t]]),
            "history_size": len(self._event_history),
            "max_history": self._max_history,
        }


# Global event bus instance
event_bus = EventBus.get_instance()


def subscribe(event_type: EventType, handler: Callable, async_handler: bool = False) -> None:
    """Convenience function to subscribe to events."""
    event_bus.subscribe(event_type, handler, async_handler)


def unsubscribe(event_type: EventType, handler: Callable) -> None:
    """Convenience function to unsubscribe from events."""
    event_bus.unsubscribe(event_type, handler)


async def publish(event_type: EventType, data: dict[str, Any] = None, source: str = "") -> None:
    """Convenience function to publish events."""
    await event_bus.publish(event_type, data, source)


def publish_sync(event_type: EventType, data: dict[str, Any] = None, source: str = "") -> None:
    """Convenience function to publish synchronous events."""
    event_bus.publish_sync(event_type, data, source)
