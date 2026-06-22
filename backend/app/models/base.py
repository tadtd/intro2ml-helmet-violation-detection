from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from ..violation_logic import Detection


class OnnxDetectionModel(ABC):
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )
        self.input_name = self.session.get_inputs()[0].name

    def preprocess(self, frame: np.ndarray, size: int = 640) -> np.ndarray:
        resized = cv2.resize(frame, (size, size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32) / 255.0
        return np.transpose(tensor, (2, 0, 1))[None, ...]

    @abstractmethod
    def predict(self, frame: np.ndarray) -> list[Detection]:
        """Return normalized detections for one BGR frame."""
