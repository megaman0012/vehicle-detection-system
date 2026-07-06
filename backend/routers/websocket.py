from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.websocket_service import manager, websocket_endpoint

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint_route(websocket: WebSocket, client_id: int):
    await websocket_endpoint(websocket)