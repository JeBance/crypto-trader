"""WebSocket manager for realtime connections."""

import asyncio
import logging
import json
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager.
    
    Manages multiple WebSocket connections and provides
    methods for broadcasting messages to all or specific clients.
    
    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast({"type": "price", "data": {...}})
    """
    
    def __init__(self):
        # Active connections: list of (websocket, client_id)
        self._connections: list[tuple[WebSocket, str]] = []
        # Subscriptions: client_id -> set of channels
        self._subscriptions: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str = "default") -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        
        async with self._lock:
            self._connections.append((websocket, client_id))
            if client_id not in self._subscriptions:
                self._subscriptions[client_id] = {"*"}  # Subscribe to all by default
            
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Send welcome message
        await self.send_personal(
            {
                "type": "connected",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            client_id,
        )
    
    def disconnect(self, client_id: str) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            client_id: Client identifier
        """
        async def _remove():
            async with self._lock:
                self._connections = [
                    (ws, cid) for ws, cid in self._connections if cid != client_id
                ]
                self._subscriptions.pop(client_id, None)
        
        asyncio.create_task(_remove())
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def send_personal(self, message: dict[str, Any], client_id: str) -> None:
        """
        Send a message to a specific client.
        
        Args:
            message: Message data
            client_id: Target client identifier
        """
        async with self._lock:
            for websocket, cid in self._connections:
                if cid == client_id:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending to {client_id}: {e}")
                        self.disconnect(client_id)
    
    async def broadcast(self, message: dict[str, Any], channel: str = "*") -> None:
        """
        Broadcast a message to all subscribed clients.
        
        Args:
            message: Message data
            channel: Channel name (default: "*" for all)
        """
        async with self._lock:
            for websocket, client_id in self._connections.copy():
                # Check if client is subscribed to channel
                client_subs = self._subscriptions.get(client_id, set())
                if "*" in client_subs or channel in client_subs:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {client_id}: {e}")
    
    async def subscribe(self, client_id: str, channel: str) -> None:
        """
        Subscribe a client to a channel.
        
        Args:
            client_id: Client identifier
            channel: Channel name
        """
        async with self._lock:
            if client_id not in self._subscriptions:
                self._subscriptions[client_id] = set()
            self._subscriptions[client_id].add(channel)
        
        logger.info(f"Client {client_id} subscribed to channel: {channel}")
    
    async def unsubscribe(self, client_id: str, channel: str) -> None:
        """
        Unsubscribe a client from a channel.
        
        Args:
            client_id: Client identifier
            channel: Channel name
        """
        async with self._lock:
            if client_id in self._subscriptions:
                self._subscriptions[client_id].discard(channel)
        
        logger.info(f"Client {client_id} unsubscribed from channel: {channel}")
    
    def get_stats(self) -> dict:
        """
        Get connection manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_connections": len(self._connections),
            "channels": {
                cid: list(subs) for cid, subs in self._subscriptions.items()
            },
        }


# Global connection manager instance
ws_manager = ConnectionManager()


# Channel constants
CHANNEL_ORDERS = "orders"
CHANNEL_POSITIONS = "positions"
CHANNEL_SIGNALS = "signals"
CHANNEL_PRICES = "prices"
CHANNEL_TRADES = "trades"
