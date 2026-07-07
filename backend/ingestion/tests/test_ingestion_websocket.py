import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock settings before importing app
from common.config import Settings
dummy_settings = Settings(
    supabase_jwt_secret="dummy-secret",
    supabase_url="https://dummy.supabase.co",
    supabase_anon_key="dummy",
    supabase_service_role_key="dummy"
)

with patch("common.config.get_settings", return_value=dummy_settings):
    from ingestion.src.main import app

client = TestClient(app)


def test_camera_websocket():
    with client.websocket_connect("/ws/camera?id=cam-01") as websocket:
        # Receive the first frame
        data = websocket.receive_bytes()
        assert len(data) > 0
        # It should be JPEG bytes starting with standard JPEG SOI marker (0xFFD8)
        assert data.startswith(b"\xff\xd8")
