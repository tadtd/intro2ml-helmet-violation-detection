from typing import Any

from common.db import DBError
from common.db.client import get_supabase_client
from common.db.constants import normalize_model_name
from common.db.records import ViolationInsert


def _page_range(limit: int, offset: int) -> tuple[int, int]:
    safe_limit = max(1, limit)
    safe_offset = max(0, offset)
    return safe_offset, safe_offset + safe_limit - 1


def insert_violation(
    video_id: str | None,
    user_id: str,
    track_id: int,
    model_name: str,
    image_url: str,
    confidence: float,
    video_offset: float,
) -> str:
    """Insert a helmet violation row and return the new row id."""
    if not 0 <= confidence <= 1:
        raise DBError("confidence must be between 0 and 1")

    try:
        payload: ViolationInsert = {
            "video_id": video_id,
            "user_id": user_id,
            "track_id": track_id,
            "model_used": normalize_model_name(model_name),
            "image_url": image_url,
            "confidence": confidence,
            "video_offset": video_offset,
        }
        response = get_supabase_client().table("violations").insert(payload).execute()
        data = response.data or []
        if not data:
            raise DBError("Violation insert returned no data")
        return str(data[0]["id"])
    except DBError:
        raise
    except ValueError as exc:
        raise DBError(str(exc)) from exc
    except Exception as exc:
        raise DBError("Failed to insert violation") from exc


def list_violations(
    video_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List violation rows with optional video filtering and pagination."""
    try:
        start, end = _page_range(limit, offset)
        query = (
            get_supabase_client()
            .table("violations")
            .select("*")
            .order("timestamp", desc=True)
            .range(start, end)
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
        start, end = _page_range(limit, offset)
        response = (
            get_supabase_client()
            .table("violations")
            .select("*")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
            .range(start, end)
            .execute()
        )
        return list(response.data or [])
    except Exception as exc:
        raise DBError("Failed to list user violations") from exc