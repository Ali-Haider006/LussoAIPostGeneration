from fastapi import APIRouter
from app.sockets.websocket_manager import manager

router = APIRouter()

@router.get("/ws-health")
async def websocket_health():
    return {
        "status": "ok",
        "active_connections": len(manager.active_connections)
    }