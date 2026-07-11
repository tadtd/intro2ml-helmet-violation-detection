from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from jose import JWTError

from common.auth import verify_supabase_access_token
from common.config import Settings


settings = Settings(
    supabase_jwt_secret="dummy-secret",
    supabase_url="https://dummy.supabase.co",
    supabase_anon_key="dummy",
    supabase_service_role_key="dummy",
)


@patch("common.auth.jwt.decode")
def test_verify_supabase_access_token_uses_local_hs256_decode(mock_decode):
    mock_decode.return_value = {"sub": "user-123", "aud": "authenticated"}

    payload = verify_supabase_access_token("token", settings)

    assert payload == {"sub": "user-123", "aud": "authenticated"}
    mock_decode.assert_called_once_with(
        "token",
        "dummy-secret",
        algorithms=["HS256"],
        audience="authenticated",
    )


@patch("common.auth.get_supabase_client")
@patch("common.auth.jwt.decode")
def test_verify_supabase_access_token_falls_back_to_supabase_auth(mock_decode, mock_client):
    mock_decode.side_effect = JWTError("The specified alg value is not allowed")
    mock_supabase = MagicMock()
    mock_supabase.auth.get_user.return_value = SimpleNamespace(
        user=SimpleNamespace(id="user-456", email="operator@example.com")
    )
    mock_client.return_value = mock_supabase

    payload = verify_supabase_access_token("Bearer asymmetric-token", settings)

    assert payload == {
        "sub": "user-456",
        "email": "operator@example.com",
        "aud": "authenticated",
    }
    mock_supabase.auth.get_user.assert_called_once_with("asymmetric-token")