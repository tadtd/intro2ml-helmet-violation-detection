import numpy as np

from .base import OnnxDetectionModel
from ..tracker import IoUTracker
from ..violation_logic import Detection


class FasterRcnnOnnxModel(OnnxDetectionModel):
    def __init__(self, model_path: str) -> None:
        super().__init__(model_path)
        self.tracker = IoUTracker()

    def predict(self, frame: np.ndarray) -> list[Detection]:
        outputs = self.session.run(None, {self.input_name: self.preprocess(frame)})
        detections = _normalize_fasterrcnn_outputs(outputs)
        tracks = self.tracker.update(
            [item.box for item in detections if item.class_name == "motorbike"],
        )
        by_box = {track.box: track.track_id for track in tracks}
        return [
            Detection(
                class_name=item.class_name,
                box=item.box,
                confidence=item.confidence,
                track_id=by_box.get(item.box),
            )
            for item in detections
        ]


def _normalize_fasterrcnn_outputs(outputs: list[np.ndarray]) -> list[Detection]:
    _ = outputs
    return []
