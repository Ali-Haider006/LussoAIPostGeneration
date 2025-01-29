from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def send_progress(self, client_id: str, current: int, total: int, post_data: dict = None):
        if client_id in self.active_connections:
            message = {
                "type": "progress",
                "current": current,
                "total": total,
                "post_data": post_data
            }
            await self.active_connections[client_id].send_text(json.dumps(message))

    async def send_error(self, client_id: str, error: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps({
                "type": "error",
                "message": error
            }))

manager = ConnectionManager()