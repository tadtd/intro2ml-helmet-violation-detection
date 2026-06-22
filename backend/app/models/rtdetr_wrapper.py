import numpy as np

from .base import OnnxDetectionModel
from ..violation_logic import Detection


class RtDetrOnnxModel(OnnxDetectionModel):
    def predict(self, frame: np.ndarray) -> list[Detection]:
        outputs = self.session.run(None, {self.input_name: self.preprocess(frame)})
        return _normalize_rtdetr_outputs(outputs)


def _normalize_rtdetr_outputs(outputs: list[np.ndarray]) -> list[Detection]:
    _ = outputs
    return []
