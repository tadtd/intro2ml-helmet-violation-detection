from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Literal

import numpy as np
import onnxruntime as ort

DetectionClass = Literal["motorbike", "helmet", "non-helmet"]
ModelName = Literal["yolo", "rtdetr", "fasterrcnn"]

VALID_CLASSES: set[str] = {"motorbike", "helmet", "non-helmet"}
VALID_MODELS: set[str] = {"yolo", "rtdetr", "fasterrcnn"}


@dataclass(frozen=True, slots=True)
class Detection:
    class_name: DetectionClass
    box: tuple[float, float, float, float]
    confidence: float
    track_id: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "class_name": self.class_name,
            "box": list(self.box),
            "confidence": float(self.confidence),
            "track_id": self.track_id,
        }

    def validate(self, width: int | None = None, height: int | None = None) -> None:
        if self.class_name not in VALID_CLASSES:
            raise ValueError(f"Invalid class_name: {self.class_name}")
        if len(self.box) != 4:
            raise ValueError("box must have 4 values: (x1, y1, x2, y2)")

        x1, y1, x2, y2 = (float(value) for value in self.box)
        if not all(isfinite(value) for value in (x1, y1, x2, y2)):
            raise ValueError(f"box contains non-finite coordinates: {self.box}")
        if x2 < x1 or y2 < y1:
            raise ValueError(f"Invalid box coordinates: {self.box}")
        if width is not None and not (0.0 <= x1 <= width and 0.0 <= x2 <= width):
            raise ValueError(f"box x coordinates outside image width {width}: {self.box}")
        if height is not None and not (0.0 <= y1 <= height and 0.0 <= y2 <= height):
            raise ValueError(f"box y coordinates outside image height {height}: {self.box}")

        confidence = float(self.confidence)
        if not isfinite(confidence) or not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


class BaseDetector(ABC):
    @abstractmethod
    def predict(self, image: np.ndarray) -> list[Detection]:
        """Run inference on one OpenCV BGR image and return normalized detections."""
        raise NotImplementedError


class OnnxDetectionModel(BaseDetector):
    def __init__(self, model_path: str | Path, providers: list[str] | None = None) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=providers or ["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name

    @abstractmethod
    def predict(self, image: np.ndarray) -> list[Detection]:
        raise NotImplementedError


def validate_image(image: np.ndarray) -> None:
    if not isinstance(image, np.ndarray):
        raise ValueError("image must be a numpy.ndarray")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"image must have shape [H, W, 3], got {image.shape}")
    if image.shape[0] <= 0 or image.shape[1] <= 0:
        raise ValueError(f"image dimensions must be positive, got {image.shape}")
