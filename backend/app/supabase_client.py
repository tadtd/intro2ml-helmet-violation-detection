from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured",
        )
    return create_client(
        str(settings.supabase_url),
        settings.supabase_service_role_key,
    )


def insert_video(
    *,
    user_id: str,
    filename: str,
    model_name: str,
    status: str = "pending",
) -> dict[str, Any]:
    response = (
        get_supabase_admin()
        .table("videos")
        .insert(
            {
                "user_id": user_id,
                "filename": filename,
                "model_used": model_name,
                "status": status,
            },
        )
        .execute()
    )
    return response.data[0]


def list_user_violations(user_id: str) -> list[dict[str, Any]]:
    response = (
        get_supabase_admin()
        .table("violations")
        .select("*")
        .eq("user_id", user_id)
        .order("timestamp", desc=True)
        .execute()
    )
    return list(response.data)
