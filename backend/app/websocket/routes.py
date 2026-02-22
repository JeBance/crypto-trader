"""WebSocket API routes."""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.websocket.manager import ConnectionManager, ws_manager, CHANNEL_ORDERS, CHANNEL_POSITIONS, CHANNEL_SIGNALS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    client_id: str = Query("default", description="Client identifier"),
    channels: Optional[str] = Query(None, description="Comma-separated channels to subscribe"),
):
    """
    WebSocket endpoint for realtime updates.
    
    Connect to receive realtime updates about:
    - Orders (channel: orders)
    - Positions (channel: positions)
    - Signals (channel: signals)
    - Prices (channel: prices)
    
    Query parameters:
    - client_id: Unique client identifier
    - channels: Comma-separated list of channels to subscribe
    """
    # Parse channels
    subscribe_channels = []
    if channels:
        subscribe_channels = [c.strip() for c in channels.split(",")]
    
    # Connect client
    await ws_manager.connect(websocket, client_id)
    
    # Subscribe to requested channels
    for channel in subscribe_channels:
        await ws_manager.subscribe(client_id, channel)
    
    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client commands
            try:
                message = eval(data) if isinstance(data, str) else data
                if isinstance(message, dict):
                    action = message.get("action")
                    
                    if action == "subscribe":
                        channel = message.get("channel")
                        if channel:
                            await ws_manager.subscribe(client_id, channel)
                            await ws_manager.send_personal(
                                {"type": "subscribed", "channel": channel},
                                client_id,
                            )
                    
                    elif action == "unsubscribe":
                        channel = message.get("channel")
                        if channel:
                            await ws_manager.unsubscribe(client_id, channel)
                            await ws_manager.send_personal(
                                {"type": "unsubscribed", "channel": channel},
                                client_id,
                            )
                    
                    elif action == "ping":
                        await ws_manager.send_personal(
                            {"type": "pong", "timestamp": __import__("datetime").datetime.utcnow().isoformat()},
                            client_id,
                        )
                    
            except Exception as e:
                logger.debug(f"Error processing client message: {e}")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(client_id)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    """
    return ws_manager.get_stats()
