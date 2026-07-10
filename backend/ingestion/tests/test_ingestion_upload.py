import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
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


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ingestion"}


@patch("ingestion.src.main.upload_video_to_storage")
@patch("ingestion.src.main.insert_video")
@patch("ingestion.src.main.celery_app.send_task")
@patch("ingestion.src.main.verify_supabase_access_token")
def test_upload_video(mock_verify_token, mock_send_task, mock_insert, mock_upload):
    # Mock authentication
    mock_verify_token.return_value = {"sub": "user-123", "role": "operator"}
    mock_upload.return_value = "raw/user-123/video.mp4"
    mock_insert.return_value = "video-456"
    
    mock_task = MagicMock()
    mock_task.id = "task-789"
    mock_send_task.return_value = mock_task

    # Send upload request
    response = client.post(
        "/upload",
        headers={"Authorization": "Bearer dummy-token"},
        files={"video": ("test.mp4", b"dummy-video-content", "video/mp4")},
        data={"model_name": "yolo"}
    )
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["video_id"] == "video-456"
    assert json_data["task_id"] == "task-789"
    assert json_data["status"] == "queued"
    
    mock_upload.assert_called_once()
    mock_insert.assert_called_once()
    mock_send_task.assert_called_once_with(
        "process_video",
        kwargs={
            "video_id": "video-456",
            "storage_path": "raw/user-123/video.mp4",
            "filename": "test.mp4",
            "model_name": "yolo",
            "user_id": "user-123"
        },
        queue="inference"
    )
