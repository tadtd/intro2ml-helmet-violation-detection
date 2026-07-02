from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.models.base import Detection, ModelName, VALID_MODELS, validate_image


def _env_flag(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _stub_detections(image: np.ndarray) -> list[Detection]:
    h, w = image.shape[:2]
    detections = [
        Detection(
            class_name="motorbike",
            box=(0.20 * w, 0.42 * h, 0.78 * w, 0.95 * h),
            confidence=0.90,
        ),
        Detection(
            class_name="non-helmet",
            box=(0.42 * w, 0.18 * h, 0.52 * w, 0.34 * h),
            confidence=0.86,
        ),
    ]
    for detection in detections:
        detection.validate(width=w, height=h)
    return detections


def _weights_dir() -> Path:
    settings = get_settings()
    path = Path(settings.model_dir)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path


@lru_cache(maxsize=3)
def get_detector(model_name: str):
    from app.models.fasterrcnn_wrapper import FasterRcnnOnnxModel
    from app.models.rtdetr_wrapper import RtDetrOnnxModel
    from app.models.yolo_wrapper import YoloOnnxModel

    weights = _weights_dir()
    if model_name == "yolo":
        return YoloOnnxModel(weights / "yolo_best.onnx")
    if model_name == "rtdetr":
        return RtDetrOnnxModel(weights / "rtdetr_best.onnx")
    if model_name == "fasterrcnn":
        return FasterRcnnOnnxModel(weights / "fasterrcnn_best.onnx")
    raise ValueError(f"Unsupported model_name: {model_name}")


def run_inference(image: np.ndarray, model_name: ModelName | str) -> list[Detection]:
    validate_image(image)
    if model_name not in VALID_MODELS:
        raise ValueError(f"Unsupported model_name: {model_name}")

    import os

    if _env_flag(os.getenv("USE_STUB_INFERENCE"), default=False):
        return _stub_detections(image)

    detector = get_detector(model_name)
    detections = detector.predict(image)
    h, w = image.shape[:2]
    for detection in detections:
        detection.validate(width=w, height=h)
    return detections
