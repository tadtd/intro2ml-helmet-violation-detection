import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# We mock config/settings before importing retention
from common.config import Settings
dummy_settings = Settings(
    supabase_jwt_secret="dummy-secret",
    supabase_url="https://dummy.supabase.co",
    supabase_anon_key="dummy",
    supabase_service_role_key="dummy",
    supabase_video_bucket="videos"
)

with patch("common.config.get_settings", return_value=dummy_settings):
    from orchestration.src.retention import run_retention_check


@patch("orchestration.src.retention.get_supabase_client")
def test_run_retention_check(mock_supabase):
    # Setup mock query for videos older than 3 days
    mock_query = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "old-vid1", "storage_path": "raw/user1/test1.mp4"},
        {"id": "old-vid2", "storage_path": "raw/user1/test2.mp4"}
    ]
    mock_query.select.return_value = mock_query
    mock_query.lt.return_value = mock_query
    mock_query.execute.return_value = mock_response
    mock_supabase.return_value.table.return_value = mock_query

    # Mock storage client for deletion
    mock_storage = MagicMock()
    mock_supabase.return_value.storage = mock_storage

    # Run retention check
    run_retention_check()

    # Verify that storage deletion was called for the video paths
    mock_storage.from_.return_value.remove.assert_any_call(["raw/user1/test1.mp4"])
    mock_storage.from_.return_value.remove.assert_any_call(["raw/user1/test2.mp4"])

    # Verify that video status updates were sent
    mock_supabase.return_value.table.return_value.update.assert_any_call({"storage_path": "deleted"})
