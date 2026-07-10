"""Verification of Supabase-issued access tokens.

Supabase signs access tokens with asymmetric JWT signing keys (ES256/RS256) and
publishes the public keys via JWKS. Older projects still use the shared HS256
secret. Both are accepted; any other algorithm is rejected to prevent an
attacker from downgrading the signature check (alg confusion).
"""

import json
import threading
import urllib.request

from jose import JWTError, jwt

from common.config import get_settings

_ASYMMETRIC_ALGORITHMS = frozenset({"ES256", "RS256"})

_jwks_lock = threading.Lock()
_jwks_keys: list[dict] | None = None


def _jwks_url() -> str:
    return f"{str(get_settings().supabase_url).rstrip('/')}/auth/v1/.well-known/jwks.json"


def _signing_key(kid: str, refresh: bool = False) -> dict | None:
    """Look up a JWKS public key by kid, refetching once if the kid is unknown."""
    global _jwks_keys

    with _jwks_lock:
        if refresh or _jwks_keys is None:
            with urllib.request.urlopen(_jwks_url(), timeout=5) as response:
                _jwks_keys = json.loads(response.read()).get("keys", [])
        keys = _jwks_keys

    for key in keys:
        if key.get("kid") == kid:
            return key

    # An unknown kid means the project rotated its signing key: refetch once.
    return None if refresh else _signing_key(kid, refresh=True)


def decode_supabase_jwt(token: str) -> dict:
    """Verify a Supabase access token and return its claims.

    Raises JWTError if the token is invalid, or OSError if the JWKS cannot be
    fetched (in which case the token's validity is simply unknown).
    """
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")

    if algorithm in _ASYMMETRIC_ALGORITHMS:
        key = _signing_key(header.get("kid"))
        if key is None:
            raise JWTError(f"No JWKS key matches kid {header.get('kid')}")
    elif algorithm == "HS256":
        key = get_settings().supabase_jwt_secret
        if not key:
            raise JWTError("SUPABASE_JWT_SECRET is not configured")
    else:
        raise JWTError(f"Unsupported token algorithm {algorithm}")

    return jwt.decode(token, key, algorithms=[algorithm], audience="authenticated")
