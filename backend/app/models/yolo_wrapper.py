import numpy as np

from .base import OnnxDetectionModel
from ..violation_logic import Detection


class YoloOnnxModel(OnnxDetectionModel):
    def predict(self, frame: np.ndarray) -> list[Detection]:
        outputs = self.session.run(None, {self.input_name: self.preprocess(frame)})
        return _normalize_ultralytics_outputs(outputs)


def _normalize_ultralytics_outputs(outputs: list[np.ndarray]) -> list[Detection]:
    # Project-specific class mapping and NMS should be completed after exporting weights.
    _ = outputs
    return []
