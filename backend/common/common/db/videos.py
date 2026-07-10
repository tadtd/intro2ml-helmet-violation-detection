from typing import Any

from common.db import DBError
from common.db.client import get_supabase_client
from common.db.constants import VideoStatus, normalize_model_name
from common.db.records import VideoInsert


def insert_video(
    user_id: str,
    filename: str,
    model_name: str,
    storage_path: str,
    content_type: str | None = None,
) -> str:
    """Insert a video row and return the generated video id."""
    try:
        payload: VideoInsert = {
            "user_id": user_id,
            "filename": filename,
            "model_used": normalize_model_name(model_name),
            "storage_path": storage_path,
            "content_type": content_type,
        }
        response = get_supabase_client().table("videos").insert(payload).execute()
        data = response.data or []
        if not data:
            raise DBError("Video insert returned no data")
        return str(data[0]["id"])
    except DBError:
        raise
    except ValueError as exc:
        raise DBError(str(exc)) from exc
    except Exception as exc:
        raise DBError("Failed to insert video") from exc


def update_video_status(video_id: str, status: VideoStatus) -> None:
    """Update a video's processing status."""
    try:
        get_supabase_client().table("videos").update({"status": status}).eq("id", video_id).execute()
    except Exception as exc:
        raise DBError("Failed to update video status") from exc


def get_video(video_id: str) -> dict[str, Any]:
    """Fetch a single video row by id."""
    try:
        response = get_supabase_client().table("videos").select("*").eq("id", video_id).single().execute()
        if not response.data:
            raise DBError("Video not found")
        return dict(response.data)
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to fetch video") from exc