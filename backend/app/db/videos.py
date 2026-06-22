from typing import Any

from app.db import DBError
from app.db.client import get_supabase_client


def insert_video(
    user_id: str,
    filename: str,
    model_used: str,
    storage_path: str,
    content_type: str | None = None,
) -> str:
    """Insert a video row and return the generated video id."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("videos")
            .insert(
                {
                    "user_id": user_id,
                    "filename": filename,
                    "model_used": model_used,
                    "storage_path": storage_path,
                    "content_type": content_type,
                }
            )
            .execute()
        )
        data = response.data or []
        if not data:
            raise DBError("Video insert returned no data")
        return str(data[0]["id"])
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to insert video") from exc


def update_video_status(video_id: str, status: str) -> None:
    """Update the status field for a video row."""
    try:
        supabase = get_supabase_client()
        supabase.table("videos").update({"status": status}).eq("id", video_id).execute()
    except Exception as exc:
        raise DBError("Failed to update video status") from exc


def get_video(video_id: str) -> dict[str, Any]:
    """Fetch a single video row by id."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("videos").select("*").eq("id", video_id).single().execute()
        if not response.data:
            raise DBError("Video not found")
        return dict(response.data)
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to fetch video") from exc
