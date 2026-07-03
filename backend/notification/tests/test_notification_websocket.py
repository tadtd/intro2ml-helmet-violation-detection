import pytest
import json
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
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
    from notification.src.main import app, active_connections, broadcast

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "notification"}


@pytest.mark.anyio
async def test_websocket_broadcast():
    # Mock a websocket connection
    mock_ws = AsyncMock()
    active_connections.append(mock_ws)
    
    test_msg = {"event": "new_violation_alert", "label": "non-helmet", "confidence": 0.89}
    await broadcast(test_msg)
    
    mock_ws.send_json.assert_called_once_with(test_msg)
    active_connections.clear()
