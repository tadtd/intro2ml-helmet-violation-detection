import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# We mock config/settings before importing task
from common.config import Settings
from inference.src.models.base import Detection
from inference.src.violation_logic import Violation

dummy_settings = Settings(
    supabase_jwt_secret="dummy-secret",
    supabase_url="https://dummy.supabase.co",
    supabase_anon_key="dummy",
    supabase_service_role_key="dummy"
)

with patch("common.config.get_settings", return_value=dummy_settings):
    from inference.src.worker import process_video


@patch("inference.src.worker.get_supabase_client")
@patch("inference.src.worker.update_video_status")
@patch("inference.src.worker.insert_violation")
@patch("inference.src.worker.upload_crop")
@patch("inference.src.worker.cv2.VideoCapture")
@patch("inference.src.worker.redis.from_url")
@patch("inference.src.worker.find_violations")
@patch.dict("os.environ", {"USE_STUB_INFERENCE": "true"})
def test_process_video_pipeline(
    mock_find_violations,
    mock_redis,
    mock_video_capture,
    mock_upload_crop,
    mock_insert_violation,
    mock_update_status,
    mock_supabase_client
):
    # Mock video capture returning 1 mock frame
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: {
        3: 640.0, # CAP_PROP_FRAME_WIDTH
        4: 360.0, # CAP_PROP_FRAME_HEIGHT
        5: 30.0,  # CAP_PROP_FPS
        7: 1.0    # CAP_PROP_FRAME_COUNT
    }.get(prop, 0.0)
    
    # Return (True, frame) once, then (False, None)
    dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
    mock_cap.read.side_effect = [(True, dummy_frame), (False, None)]
    
    mock_video_capture.return_value = mock_cap

    # Mock DB/Storage
    mock_upload_crop.return_value = "https://dummy.supabase.co/storage/v1/object/public/violations/crops/user1/vid_track.jpg"
    mock_insert_violation.return_value = "violation-111"

    # Mock finding a violation
    mock_violation = Violation(
        motorbike=Detection(class_name="motorbike", box=(100, 100, 200, 200), confidence=0.9),
        non_helmet=Detection(class_name="non-helmet", box=(120, 120, 150, 150), confidence=0.8)
    )
    mock_find_violations.return_value = [mock_violation]

    # Call task function directly
    res = process_video(
        video_id="video-123",
        storage_path="raw/user1/video.mp4",
        filename="test.mp4",
        model_name="yolo",
        user_id="user1"
    )

    assert res["status"] == "done"
    assert res["video_id"] == "video-123"

    # Verify video statuses are updated
    mock_update_status.assert_any_call("video-123", "processing")
    mock_update_status.assert_any_call("video-123", "done")

    # Verify violation is inserted
    mock_insert_violation.assert_called()
    mock_upload_crop.assert_called()
