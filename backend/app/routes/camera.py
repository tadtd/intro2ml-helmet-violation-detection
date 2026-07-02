from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["camera"])


@router.websocket("/ws/camera")
async def camera_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"status": "connected"})
    try:
        while True:
            await websocket.receive_bytes()
            await websocket.send_json({"status": "received", "violations": []})
    except WebSocketDisconnect:
        return
