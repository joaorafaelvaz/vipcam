import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.redis_service import redis_service

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info("WebSocket client connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)
        logger.info("WebSocket client disconnected", total=len(self.active_connections))

    def subscribe(self, websocket: WebSocket, camera_ids: list[str]):
        if websocket in self.active_connections:
            if "all" in camera_ids:
                self.active_connections[websocket] = {"all"}
            else:
                self.active_connections[websocket].update(camera_ids)

    def unsubscribe(self, websocket: WebSocket, camera_ids: list[str]):
        if websocket in self.active_connections:
            self.active_connections[websocket] -= set(camera_ids)

    async def broadcast(self, camera_id: str, message: str):
        disconnected = []
        for ws, subscriptions in self.active_connections.items():
            if "all" in subscriptions or camera_id in subscriptions:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


manager = ConnectionManager()


async def redis_listener():
    """Background task that listens to Redis pub/sub and broadcasts to WebSocket clients."""
    while True:
        try:
            pubsub = await redis_service.psubscribe("vipcam:frames:*")
            logger.info("Redis pub/sub listener started")
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    data = message.get("data", "")
                    if isinstance(data, str):
                        try:
                            parsed = json.loads(data)
                            camera_id = parsed.get("camera_id", "")
                            await manager.broadcast(str(camera_id), data)
                        except json.JSONDecodeError:
                            pass
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error("Redis listener error, reconnecting in 3s", error=str(e))
            await asyncio.sleep(3)


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Default: subscribe to all cameras
    manager.subscribe(websocket, ["all"])

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                cameras = msg.get("cameras", [])

                if action == "subscribe":
                    manager.subscribe(websocket, cameras)
                elif action == "unsubscribe":
                    manager.unsubscribe(websocket, cameras)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
