import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# We mock config/settings before importing app
from common.config import Settings
dummy_settings = Settings(
    supabase_jwt_secret="dummy-secret",
    supabase_url="https://dummy.supabase.co",
    supabase_anon_key="dummy",
    supabase_service_role_key="dummy"
)

with patch("common.config.get_settings", return_value=dummy_settings):
    # Disable middleware to test queries directly or mock it
    from dashboard.src.main import app

client = TestClient(app)


@patch("dashboard.src.queries.get_supabase_client")
@patch("dashboard.src.middleware.grpc.aio.insecure_channel")
def test_list_violations_admin(mock_channel, mock_supabase):
    # Mock gRPC VerifyToken returning an admin user
    from unittest.mock import AsyncMock
    mock_stub = MagicMock()
    mock_resp = MagicMock()
    mock_resp.is_valid = True
    mock_resp.user_id = "admin-123"
    mock_resp.role = "admin"
    mock_stub.VerifyToken = AsyncMock(return_value=mock_resp)
    
    # Setup async context manager mock for channel
    mock_channel_instance = MagicMock()
    mock_channel_instance.__aenter__.return_value = mock_channel_instance
    mock_channel.return_value = mock_channel_instance
    
    # We patch VerifyToken inside middleware directly or mock the auth return value
    with patch("dashboard.src.middleware.auth_pb2_grpc.AuthServiceStub", return_value=mock_stub):
        # Mock database query response
        mock_response = MagicMock()
        mock_response.data = [
            {"id": "v1", "user_id": "operator-456", "model_used": "yolo", "timestamp": "2026-07-04T00:00:00Z"},
            {"id": "v2", "user_id": "admin-123", "model_used": "yolo", "timestamp": "2026-07-04T01:00:00Z"}
        ]
        
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_response
        
        mock_supabase.return_value.table.return_value.select.return_value = mock_query

        # Send request
        response = client.get(
            "/violations?model=yolo",
            headers={"Authorization": "Bearer admin-token"}
        )
        
        assert response.status_code == 200
        json_data = response.json()
        assert len(json_data["items"]) == 2
        # Admin should not have RLS filter eq("user_id") called
        # mock_query.eq is called once for model
        mock_query.eq.assert_called_once_with("model_used", "YOLO")
