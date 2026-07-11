import logging
from typing import Annotated, Any
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError

from common.auth import verify_supabase_access_token
from common.config import get_settings
from common.db import DBError
from common.db.client import get_supabase_client
from common.db.storage import get_video_url, upload_video as upload_video_to_storage
from common.db.videos import get_video, insert_video
from common.db.constants import normalize_model_name
from common.celery import celery_app
from common.security import decode_supabase_jwt

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

    try:
        payload = decode_supabase_jwt(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase JWT",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch Supabase JWKS to verify the token",
        ) from exc

    return payload


# The gateway routes PathPrefix(`/api/v1/videos`) here and strips `/api/v1`,
# so every HTTP route below must live under `/videos`.
@app.post("/videos/upload")
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


def _is_admin(user_id: str) -> bool:
    try:
        response = (
            get_supabase_client()
            .table("profiles")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        return (response.data or {}).get("role") == "admin"
    except Exception:
        # Treat an unreadable profile as the least privileged role.
        return False


@app.get("/videos/jobs")
def list_jobs(
    current_user: Annotated[dict, Depends(get_current_user)],
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Videos owned by the caller, newest first. Admins see every video."""
    user_id = current_user["sub"]
    try:
        query = get_supabase_client().table("videos").select(
            "id, filename, status, model_used, created_at, processed_at"
        )
        if not _is_admin(user_id):
            query = query.eq("user_id", user_id)
        response = query.order("created_at", desc=True).limit(limit).execute()
    except Exception as exc:
        logger.error(f"Failed to list jobs: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        ) from exc

    return [
        {
            "jobId": row["id"],
            "fileName": row.get("filename"),
            "status": row.get("status"),
            "modelUsed": row.get("model_used"),
            "createdAt": row.get("created_at"),
            "completedAt": row.get("processed_at"),
        }
        for row in (response.data or [])
    ]


@app.get("/videos/{video_id}")
def get_video_detail(
    video_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """Single video, restricted to its owner unless the caller is an admin."""
    try:
        video = get_video(video_id)
    except DBError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    user_id = current_user["sub"]
    if video.get("user_id") != user_id and not _is_admin(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your video")

    # The player needs a URL it can fetch, and the video bucket is private.
    storage_path = video.get("storage_path")
    try:
        playback_url = get_video_url(storage_path) if storage_path else None
    except DBError as exc:
        logger.warning(f"Could not sign playback URL for {video_id}: {exc}")
        playback_url = None

    return {
        "id": video["id"],
        "filename": video.get("filename"),
        "status": video.get("status"),
        "modelUsed": video.get("model_used"),
        "storagePath": playback_url,
        "createdAt": video.get("created_at"),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ingestion"}
