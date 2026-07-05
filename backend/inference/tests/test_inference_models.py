import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from inference.src.models.registry import run_inference
from inference.src.models.base import Detection


@patch.dict("os.environ", {"USE_STUB_INFERENCE": "true"})
def test_stub_inference():
    # Create a dummy image
    image = np.zeros((360, 640, 3), dtype=np.uint8)
    detections = run_inference(image, "yolo")
    
    assert len(detections) == 2
    assert detections[0].class_name == "motorbike"
    assert detections[1].class_name == "non-helmet"
    
    # Check boundaries
    detections[0].validate(width=640, height=360)
    detections[1].validate(width=640, height=360)


def test_invalid_image():
    with pytest.raises(ValueError):
        run_inference(None, "yolo")
        
    with pytest.raises(ValueError):
        run_inference(np.zeros((100, 100), dtype=np.uint8), "yolo")
