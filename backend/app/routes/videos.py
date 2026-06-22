from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..auth import get_current_user
from ..supabase_client import insert_video
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

    video_row = insert_video(
        user_id=current_user["sub"],
        filename=video.filename or "uploaded-video",
        model_name=model_name,
    )
    task = process_video.delay(
        video_id=video_row["id"],
        filename=video.filename or "uploaded-video",
        model_name=model_name,
        user_id=current_user["sub"],
    )
    return {"video_id": video_row["id"], "task_id": task.id, "status": "queued"}
