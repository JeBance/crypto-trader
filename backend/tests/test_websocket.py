"""Tests for WebSocket Connection Manager."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.websocket.manager import ConnectionManager, ws_manager


class TestConnectionManager:
    """Tests for WebSocket Connection Manager."""
    
    @pytest.fixture
    def manager(self):
        """Create a new connection manager."""
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connect(self, manager):
        """Test client connection."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "test_client")
        
        websocket.accept.assert_called_once()
        assert len(manager._connections) == 1
        
        # Check welcome message was sent
        websocket.send_json.assert_called()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connected"
        assert call_args["client_id"] == "test_client"
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager):
        """Test client disconnection."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "test_client")
        manager.disconnect("test_client")
        
        # Wait for async disconnect
        await asyncio.sleep(0.1)
        
        assert len(manager._connections) == 0
        assert "test_client" not in manager._subscriptions
    
    @pytest.mark.asyncio
    async def test_send_personal(self, manager):
        """Test sending message to specific client."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "client1")
        
        message = {"type": "test", "data": "hello"}
        await manager.send_personal(message, "client1")
        
        websocket.send_json.assert_called_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """Test broadcasting to all clients."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        
        message = {"type": "broadcast", "data": "all"}
        await manager.broadcast(message)
        
        assert ws1.send_json.call_count >= 1
        assert ws2.send_json.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager):
        """Test broadcasting to specific channel."""
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        await manager.connect(ws1, "client1")
        await manager.connect(ws2, "client2")
        
        # Subscribe client1 to specific channel
        await manager.subscribe("client1", "orders")
        
        message = {"type": "order_update"}
        await manager.broadcast(message, channel="orders")
        
        # client1 should receive (subscribed to "orders")
        # client2 should receive (subscribed to "*" by default)
        assert ws1.send_json.call_count >= 1
        assert ws2.send_json.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_subscribe(self, manager):
        """Test subscribing to channel."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "client1")
        await manager.subscribe("client1", "orders")
        
        assert "orders" in manager._subscriptions["client1"]
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager):
        """Test unsubscribing from channel."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "client1")
        await manager.subscribe("client1", "orders")
        await manager.unsubscribe("client1", "orders")
        
        assert "orders" not in manager._subscriptions["client1"]
    
    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """Test getting statistics."""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        
        await manager.connect(websocket, "client1")
        await manager.subscribe("client1", "orders")
        
        stats = manager.get_stats()
        
        assert stats["total_connections"] == 1
        assert "client1" in stats["channels"]
        assert "orders" in stats["channels"]["client1"]


class TestGlobalManager:
    """Tests for global ws_manager instance."""
    
    def test_global_manager_exists(self):
        """Test that global manager instance exists."""
        from app.websocket.manager import ws_manager
        assert ws_manager is not None
        assert isinstance(ws_manager, ConnectionManager)
    
    def test_channel_constants(self):
        """Test that channel constants are defined."""
        from app.websocket.manager import (
            CHANNEL_ORDERS,
            CHANNEL_POSITIONS,
            CHANNEL_SIGNALS,
            CHANNEL_PRICES,
            CHANNEL_TRADES,
        )
        
        assert CHANNEL_ORDERS == "orders"
        assert CHANNEL_POSITIONS == "positions"
        assert CHANNEL_SIGNALS == "signals"
        assert CHANNEL_PRICES == "prices"
        assert CHANNEL_TRADES == "trades"
