from typing import Any

from app.db import DBError
from app.db.client import get_supabase_client


def insert_violation(
    video_id: str | None,
    user_id: str,
    track_id: int,
    model_used: str,
    image_url: str,
) -> None:
    """Insert a helmet violation row."""
    try:
        supabase = get_supabase_client()
        supabase.table("violations").insert(
            {
                "video_id": video_id,
                "user_id": user_id,
                "track_id": track_id,
                "model_used": model_used,
                "image_url": image_url,
            }
        ).execute()
    except Exception as exc:
        raise DBError("Failed to insert violation") from exc


def list_violations(
    video_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List violation rows with optional video filtering and pagination."""
    try:
        supabase = get_supabase_client()
        safe_limit = max(1, limit)
        safe_offset = max(0, offset)
        end_index = safe_offset + safe_limit - 1

        query = (
            supabase.table("violations")
            .select("*")
            .order("timestamp", desc=True)
            .range(safe_offset, end_index)
        )
        if video_id is not None:
            query = query.eq("video_id", video_id)

        response = query.execute()
        return list(response.data or [])
    except Exception as exc:
        raise DBError("Failed to list violations") from exc


def list_user_violations(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List violation rows for a single user with pagination."""
    try:
        supabase = get_supabase_client()
        safe_limit = max(1, limit)
        safe_offset = max(0, offset)
        end_index = safe_offset + safe_limit - 1

        response = (
            supabase.table("violations")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .range(safe_offset, end_index)
            .execute()
        )
        return list(response.data or [])
    except Exception as exc:
        raise DBError("Failed to list user violations") from exc
