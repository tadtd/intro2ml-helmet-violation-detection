import logging
from typing import Any

from jose import JWTError, jwt

from common.config import Settings, get_settings
from common.db.client import get_supabase_client

logger = logging.getLogger("common.auth")


def _extract_user_id(user: Any) -> str | None:
    if user is None:
        return None
    if isinstance(user, dict):
        return user.get("id") or user.get("sub")
    return getattr(user, "id", None) or getattr(user, "sub", None)


def _verify_with_supabase(token: str) -> dict[str, Any] | None:
    response = get_supabase_client().auth.get_user(token)
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
        user = response.get("user")

    user_id = _extract_user_id(user)
    if not user_id:
        return None

    email = user.get("email") if isinstance(user, dict) else getattr(user, "email", None)
    return {"sub": user_id, "email": email, "aud": "authenticated"}


def verify_supabase_access_token(token: str, settings: Settings | None = None) -> dict[str, Any] | None:
    """Verify a Supabase access token.

    Prefer local HS256 verification for legacy Supabase JWTs. If the project uses
    asymmetric signing keys, python-jose rejects the token before signature
    verification because the algorithm is not HS256. In that case, ask Supabase
    Auth to validate the access token and return the authenticated user id.
    """
    if token.startswith("Bearer "):
        token = token[len("Bearer ") :]

    if not token:
        return None

    settings = settings or get_settings()

    if settings.supabase_jwt_secret:
        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except JWTError as exc:
            logger.info("Local Supabase JWT verification failed; trying Supabase Auth: %s", exc)

    try:
        return _verify_with_supabase(token)
    except Exception as exc:
        logger.warning("Supabase Auth token verification failed: %s", exc)
        return None