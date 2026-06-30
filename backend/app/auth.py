import json
from functools import lru_cache
from typing import Annotated, Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def _supabase_auth_issuer(supabase_url: Any) -> str:
    return f"{str(supabase_url).rstrip('/')}/auth/v1"


@lru_cache(maxsize=8)
def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    with urlopen(jwks_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_jwks_key(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    return next(
        (key for key in jwks.get("keys", []) if key.get("kid") == kid),
        None,
    )


def _decode_supabase_jwt(token: str) -> dict[str, Any]:
    settings = get_settings()

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase JWT",
        ) from exc

    algorithm = header.get("alg")
    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SUPABASE_JWT_SECRET is not configured",
            )
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )

    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_URL is not configured",
        )

    kid = header.get("kid")
    if not isinstance(kid, str) or not isinstance(algorithm, str):
        raise JWTError("Missing key id or algorithm")

    issuer = _supabase_auth_issuer(settings.supabase_url)
    jwks_url = f"{issuer}/.well-known/jwks.json"

    try:
        jwks = _fetch_jwks(jwks_url)
        key = _find_jwks_key(jwks, kid)
        if key is None:
            _fetch_jwks.cache_clear()
            jwks = _fetch_jwks(jwks_url)
            key = _find_jwks_key(jwks, kid)
    except (OSError, URLError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Supabase JWKS",
        ) from exc

    if key is None:
        raise JWTError("No matching Supabase JWKS key")

    return jwt.decode(
        token,
        key,
        algorithms=[algorithm],
        audience="authenticated",
        issuer=issuer,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    try:
        payload = _decode_supabase_jwt(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase JWT",
        ) from exc

    return payload
