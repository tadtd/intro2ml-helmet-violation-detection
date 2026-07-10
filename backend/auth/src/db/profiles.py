from typing import Any

from common.db import DBError
from common.db.client import get_supabase_client


def get_profile(user_id: str) -> dict[str, Any]:
    """Fetch a single profile row, including the user's role."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("profiles")
            .select("id, role, display_name, created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not response.data:
            raise DBError("Profile not found")
        return dict(response.data)
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to fetch profile") from exc


def upsert_profile(user_id: str, full_name: str, role: str = "operator") -> None:
    """Create or update a profile row by user id."""
    try:
        supabase = get_supabase_client()
        supabase.table("profiles").upsert(
            {
                "id": user_id,
                "display_name": full_name,
                "role": role,
            },
            on_conflict="id",
        ).execute()
    except Exception as exc:
        raise DBError("Failed to upsert profile") from exc
