"""Tests for Event Bus."""

import asyncio
import pytest

from app.core.events import (
    Event,
    EventBus,
    EventType,
    event_bus,
    subscribe,
    publish,
    publish_sync,
)


@pytest.fixture
def reset_event_bus():
    """Reset event bus before each test."""
    EventBus.reset_instance()
    yield
    EventBus.reset_instance()


class TestEventBus:
    """Tests for Event Bus."""
    
    def test_singleton_instance(self, reset_event_bus):
        """Test EventBus is a singleton."""
        bus1 = EventBus.get_instance()
        bus2 = EventBus.get_instance()
        
        assert bus1 is bus2
    
    def test_subscribe_and_publish(self, reset_event_bus):
        """Test basic subscribe and publish."""
        bus = EventBus.get_instance()
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        bus.subscribe(EventType.ORDER_CREATED, handler)
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"order_id": "123"}))
        
        assert len(received_events) == 1
        assert received_events[0].type == EventType.ORDER_CREATED
        assert received_events[0].data["order_id"] == "123"
    
    @pytest.mark.asyncio
    async def test_async_handler(self, reset_event_bus):
        """Test async event handler."""
        bus = EventBus.get_instance()
        received_events = []
        
        async def async_handler(event: Event):
            received_events.append(event)
        
        bus.subscribe(EventType.ORDER_CREATED, async_handler, async_handler=True)
        await bus.publish(EventType.ORDER_CREATED, {"order_id": "456"})
        
        assert len(received_events) == 1
        assert received_events[0].data["order_id"] == "456"
    
    def test_unsubscribe(self, reset_event_bus):
        """Test unsubscribe from events."""
        bus = EventBus.get_instance()
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        bus.subscribe(EventType.ORDER_CREATED, handler)
        bus.unsubscribe(EventType.ORDER_CREATED, handler)
        
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"order_id": "789"}))
        
        assert len(received_events) == 0
    
    def test_unsubscribe_all(self, reset_event_bus):
        """Test unsubscribe all handlers."""
        bus = EventBus.get_instance()
        received_events = []
        
        def handler1(event: Event):
            received_events.append(("h1", event))
        
        def handler2(event: Event):
            received_events.append(("h2", event))
        
        bus.subscribe(EventType.ORDER_CREATED, handler1)
        bus.subscribe(EventType.ORDER_CREATED, handler2)
        
        bus.unsubscribe_all(EventType.ORDER_CREATED)
        
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"order_id": "999"}))
        
        assert len(received_events) == 0
    
    def test_event_history(self, reset_event_bus):
        """Test event history tracking."""
        bus = EventBus.get_instance()
        
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"id": 1}))
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"id": 2}))
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"id": 3}))
        
        history = bus.get_history(EventType.ORDER_CREATED)
        
        assert len(history) == 3
        assert history[0].data["id"] == 1
        assert history[2].data["id"] == 3
    
    def test_event_history_limit(self, reset_event_bus):
        """Test event history limit."""
        bus = EventBus.get_instance()
        
        # Publish more than max_history (100)
        for i in range(150):
            asyncio.run(bus.publish(EventType.ORDER_CREATED, {"id": i}))
        
        history = bus.get_history(EventType.ORDER_CREATED)
        
        assert len(history) == 100  # Max history
        assert history[0].data["id"] == 50  # Oldest is 50
    
    def test_clear_history(self, reset_event_bus):
        """Test clearing event history."""
        bus = EventBus.get_instance()
        
        asyncio.run(bus.publish(EventType.ORDER_CREATED, {"id": 1}))
        bus.clear_history()
        
        history = bus.get_history(EventType.ORDER_CREATED)
        assert len(history) == 0
    
    def test_get_stats(self, reset_event_bus):
        """Test getting event bus statistics."""
        bus = EventBus.get_instance()
        
        def handler1(event: Event):
            pass
        
        def handler2(event: Event):
            pass
        
        bus.subscribe(EventType.ORDER_CREATED, handler1)
        bus.subscribe(EventType.ORDER_FILLED, handler2)
        
        stats = bus.get_stats()
        
        assert stats["total_handlers"] == 2
        assert stats["event_types_subscribed"] == 2
        assert stats["history_size"] == 0
    
    def test_publish_sync(self, reset_event_bus):
        """Test synchronous publish."""
        bus = EventBus.get_instance()
        received_events = []
        
        def handler(event: Event):
            received_events.append(event)
        
        bus.subscribe(EventType.ORDER_CREATED, handler)
        bus.publish_sync(EventType.ORDER_CREATED, {"order_id": "sync"})
        
        assert len(received_events) == 1
        assert received_events[0].data["order_id"] == "sync"
    
    def test_event_types(self, reset_event_bus):
        """Test all event types are defined."""
        # Order events
        assert EventType.ORDER_CREATED.value == "order_created"
        assert EventType.ORDER_FILLED.value == "order_filled"
        assert EventType.ORDER_CANCELLED.value == "order_cancelled"
        
        # Position events
        assert EventType.POSITION_OPENED.value == "position_opened"
        assert EventType.POSITION_CLOSED.value == "position_closed"
        
        # Strategy events
        assert EventType.SIGNAL_GENERATED.value == "signal_generated"
        
        # System events
        assert EventType.SYSTEM_STARTED.value == "system_started"
        assert EventType.ERROR_OCCURRED.value == "error_occurred"


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_subscribe_function(self, reset_event_bus):
        """Test subscribe convenience function."""
        received = []
        
        def handler(event: Event):
            received.append(event)
        
        subscribe(EventType.ORDER_CREATED, handler)
        
        bus = EventBus.get_instance()
        assert len(bus._handlers[EventType.ORDER_CREATED]) == 1
    
    def test_publish_function(self, reset_event_bus):
        """Test publish convenience function."""
        received = []
        
        def handler(event: Event):
            received.append(event)
        
        subscribe(EventType.ORDER_CREATED, handler)
        
        asyncio.run(publish(EventType.ORDER_CREATED, {"test": "data"}))
        
        assert len(received) == 1
        assert received[0].data["test"] == "data"
