from typing import Annotated
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..auth import get_current_user
from ..db.storage import upload_video as upload_video_to_storage
from ..db.videos import insert_video
from ..tasks import process_video

router = APIRouter(prefix="/videos", tags=["videos"])

SUPPORTED_MODELS = {"yolo", "rtdetr", "fasterrcnn"}


@router.post("/upload")
async def upload_video(
    current_user: Annotated[dict, Depends(get_current_user)],
    video: UploadFile = File(...),
    model_name: str = Form("yolo"),
) -> dict[str, str]:
    if model_name not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_name must be one of: yolo, rtdetr, fasterrcnn",
        )

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

    video_id = insert_video(
        user_id=current_user["sub"],
        filename=original_filename,
        model_used=model_name,
        storage_path=storage_path,
        content_type=video.content_type,
    )
    task = process_video.delay(
        video_id=video_id,
        storage_path=storage_path,
        filename=original_filename,
        model_name=model_name,
        user_id=current_user["sub"],
    )
    return {"video_id": video_id, "task_id": task.id, "status": "queued"}
