"""WebSocket routes for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger("pollmaster.api.websocket")
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections for live poll updates."""
    
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, poll_code: str):
        await websocket.accept()
        if poll_code not in self.active_connections:
            self.active_connections[poll_code] = []
        self.active_connections[poll_code].append(websocket)
        logger.debug("websocket_connected", poll_code=poll_code)
    
    def disconnect(self, websocket: WebSocket, poll_code: str):
        if poll_code in self.active_connections:
            self.active_connections[poll_code].remove(websocket)
            if not self.active_connections[poll_code]:
                del self.active_connections[poll_code]
        logger.debug("websocket_disconnected", poll_code=poll_code)
    
    async def broadcast(self, poll_code: str, message: dict):
        if poll_code in self.active_connections:
            disconnected = []
            for connection in self.active_connections[poll_code]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, poll_code)


manager = ConnectionManager()


@router.websocket("/polls/{poll_code}")
async def poll_websocket(websocket: WebSocket, poll_code: str):
    """WebSocket endpoint for real-time poll updates."""
    await manager.connect(websocket, poll_code)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            # Echo back or process commands
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, poll_code)
    except Exception as e:
        logger.error("websocket_error", error=str(e), poll_code=poll_code)
        manager.disconnect(websocket, poll_code)
