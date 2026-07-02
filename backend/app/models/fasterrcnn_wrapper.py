from __future__ import annotations

from pathlib import Path

import numpy as np

from app.models.base import Detection, OnnxDetectionModel, validate_image
from app.models.postprocess import class_name_from_id, clip_box
from app.models.preprocess import resize_bgr_to_tensor


class FasterRcnnOnnxModel(OnnxDetectionModel):
    def __init__(
        self,
        model_path: str | Path,
        conf_threshold: float = 0.25,
        input_size: int = 640,
    ) -> None:
        super().__init__(model_path)
        self.conf_threshold = conf_threshold
        self.input_size = input_size

    def predict(self, frame: np.ndarray) -> list[Detection]:
        validate_image(frame)
        h, w = frame.shape[:2]
        tensor, scale_x, scale_y = resize_bgr_to_tensor(frame, self.input_size)
        outputs = self.session.run(None, {self.input_name: tensor})
        return normalize_fasterrcnn_outputs(
            outputs,
            width=w,
            height=h,
            scale_x=scale_x,
            scale_y=scale_y,
            conf_threshold=self.conf_threshold,
        )


def normalize_fasterrcnn_outputs(
    outputs: list[np.ndarray],
    *,
    width: int,
    height: int,
    scale_x: float,
    scale_y: float,
    conf_threshold: float,
) -> list[Detection]:
    if len(outputs) < 3:
        raise RuntimeError(f"Unsupported Faster R-CNN ONNX output count: {len(outputs)}")
    boxes = np.asarray(outputs[0])
    labels = np.asarray(outputs[1]).astype(int)
    scores = np.asarray(outputs[2])

    if boxes.ndim == 3:
        boxes = boxes[0]
    if labels.ndim > 1:
        labels = labels.reshape(-1)
    if scores.ndim > 1:
        scores = scores.reshape(-1)

    detections: list[Detection] = []
    for box, label, score in zip(boxes, labels, scores, strict=False):
        score = float(score)
        if not np.isfinite(score) or score < conf_threshold:
            continue
        class_name = class_name_from_id(int(label), background_offset=True)
        if class_name is None:
            continue
        scaled = (
            float(box[0]) * scale_x,
            float(box[1]) * scale_y,
            float(box[2]) * scale_x,
            float(box[3]) * scale_y,
        )
        clipped = clip_box(scaled, width, height)
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            continue
        detection = Detection(
            class_name=class_name,
            box=clipped,
            confidence=score,
        )
        detection.validate(width=width, height=height)
        detections.append(detection)
    return detections
