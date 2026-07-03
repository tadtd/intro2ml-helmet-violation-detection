from __future__ import annotations

from pathlib import Path

import numpy as np

from .base import Detection, OnnxDetectionModel, validate_image
from .yolo_wrapper import normalize_ultralytics_detections
from .preprocess import (
    box_from_letterbox_to_original,
    bgr_to_rgb_chw_tensor,
    letterbox_bgr,
)


class RtDetrOnnxModel(OnnxDetectionModel):
    def __init__(
        self,
        model_path: str | Path,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
        input_size: int = 640,
    ) -> None:
        super().__init__(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_size = input_size

    def predict(self, frame: np.ndarray) -> list[Detection]:
        validate_image(frame)
        h, w = frame.shape[:2]
        padded, scale, pad = letterbox_bgr(frame, self.input_size)
        tensor = bgr_to_rgb_chw_tensor(padded)
        outputs = self.session.run(None, {self.input_name: tensor})
        return normalize_ultralytics_detections(
            outputs,
            width=w,
            height=h,
            scale=scale,
            pad=pad,
            input_size=self.input_size,
            conf_threshold=self.conf_threshold,
            iou_threshold=self.iou_threshold,
        )
