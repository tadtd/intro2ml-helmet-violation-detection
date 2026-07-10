import logging
from typing import Annotated, Any
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt

from common.config import get_settings
from common.db import DBError
from common.db.storage import upload_video as upload_video_to_storage
from common.db.videos import insert_video
from common.db.constants import normalize_model_name
from common.celery import celery_app
from .websocket import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion.api")

settings = get_settings()
app = FastAPI(title="Ingestion Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase JWT",
        ) from exc

    return payload


@app.post("/upload")
async def upload_video(
    current_user: Annotated[dict, Depends(get_current_user)],
    video: UploadFile = File(...),
    model_name: str = Form("yolo"),
) -> dict[str, str]:
    try:
        normalize_model_name(model_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    original_filename = Path(video.filename or "uploaded-video").name or "uploaded-video"
    content = await video.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded video is empty",
        )

    object_path = f"{current_user['sub']}/{uuid4()}-{original_filename}"
    storage_path = upload_video_to_storage(
        content=content,
        filename=object_path,
        content_type=video.content_type,
    )

    try:
        video_id = insert_video(
            user_id=current_user["sub"],
            filename=original_filename,
            model_name=model_name,
            storage_path=storage_path,
            content_type=video.content_type,
        )
    except DBError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # Trigger Celery task
    task = celery_app.send_task(
        "process_video",
        kwargs={
            "video_id": video_id,
            "storage_path": storage_path,
            "filename": original_filename,
            "model_name": model_name,
            "user_id": current_user["sub"],
        },
        queue="inference",  # Send directly to the inference worker queue!
    )

    # Publish initial job status to Redis
    try:
        import redis
        import json
        r_client = redis.from_url(settings.redis_url)
        r_client.publish(
            "job_status_update",
            json.dumps({
                "jobId": video_id,
                "fileName": original_filename,
                "status": "pending",
                "modelUsed": model_name
            })
        )
    except Exception as e:
        logger.warning(f"Failed to publish initial job_status_update event: {e}")

    return {"video_id": video_id, "task_id": task.id, "status": "queued"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion"}


# Include WebSocket router
app.include_router(ws_router)
