from typing import Annotated

from fastapi import Depends, FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user
from .config import get_settings
from .tasks import process_video

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/videos/upload")
async def upload_video(
    current_user: Annotated[dict, Depends(get_current_user)],
    video: UploadFile = File(...),
    model_name: str = "yolo",
) -> dict[str, str]:
    task = process_video.delay(
        filename=video.filename,
        model_name=model_name,
        user_id=current_user["sub"],
    )
    return {"task_id": task.id, "status": "queued"}


@app.get("/violations")
def list_violations(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, object]:
    return {
        "items": [],
        "user_id": current_user["sub"],
        "note": "Connect Supabase query once database tables are created.",
    }


@app.websocket("/ws/camera")
async def camera_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"status": "connected"})
    try:
        while True:
            await websocket.receive_bytes()
            await websocket.send_json(
                {"status": "received", "violations": []},
            )
    except WebSocketDisconnect:
        return
