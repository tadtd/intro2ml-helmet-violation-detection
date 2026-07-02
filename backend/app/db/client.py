from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings
from app.db import DBError


@lru_cache
def _create_supabase_client() -> Client:
    """Create the backend Supabase client using the service role key."""
    settings = get_settings()
    supabase_url = settings.supabase_url
    service_role_key = settings.supabase_service_role_key

    if not supabase_url or not service_role_key:
        raise DBError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")

    try:
        return create_client(str(supabase_url), service_role_key)
    except Exception as exc:
        raise DBError("Failed to initialize Supabase client") from exc


def get_supabase_client() -> Client:
    """Return a cached Supabase service-role client."""
    return _create_supabase_client()
