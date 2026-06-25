from __future__ import annotations

from pathlib import Path

import numpy as np

from app.models.base import Detection, OnnxDetectionModel, validate_image
from app.models.postprocess import class_name_from_id, clip_box, nms
from app.models.preprocess import (
    box_from_letterbox_to_original,
    bgr_to_rgb_chw_tensor,
    letterbox_bgr,
)


class YoloOnnxModel(OnnxDetectionModel):
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


def normalize_ultralytics_detections(
    outputs: list[np.ndarray],
    *,
    width: int,
    height: int,
    scale: float,
    pad: tuple[float, float],
    input_size: int = 640,
    conf_threshold: float,
    iou_threshold: float,
) -> list[Detection]:
    raw = np.asarray(outputs[0])
    if raw.ndim == 3:
        raw = raw[0]
    if raw.size == 0:
        return []

    # Ultralytics exported NMS output is usually [x1, y1, x2, y2, score, class].
    # Some exports produce [x1, y1, x2, y2, class, score], so handle both.
    if raw.shape[-1] < 6:
        raise RuntimeError(f"Unsupported Ultralytics ONNX output shape: {raw.shape}")

    rows = raw[:, :6].astype(np.float32)
    score_col = 4
    class_col = 5
    if np.nanmax(rows[:, 4]) > 1.0 and np.nanmax(rows[:, 5]) <= 1.0:
        score_col = 5
        class_col = 4

    candidates: list[tuple[tuple[float, float, float, float], float, int]] = []
    for row in rows:
        score = float(row[score_col])
        if not np.isfinite(score) or score < conf_threshold:
            continue
        class_id = int(round(float(row[class_col])))
        class_name = class_name_from_id(class_id)
        if class_name is None:
            continue

        box = row[:4].astype(np.float32)
        if np.nanmax(box) <= 1.5:
            if box[2] < box[0] or box[3] < box[1]:
                cx, cy, bw, bh = box
                box = np.asarray(
                    [
                        cx - bw / 2,
                        cy - bh / 2,
                        cx + bw / 2,
                        cy + bh / 2,
                    ],
                    dtype=np.float32,
                )
            box *= float(input_size)
            original_box = box_from_letterbox_to_original(box, scale, pad)
        else:
            original_box = box_from_letterbox_to_original(box, scale, pad)
        clipped = clip_box(original_box, width, height)
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            continue
        candidates.append((clipped, score, class_id))

    if not candidates:
        return []

    boxes = np.asarray([item[0] for item in candidates], dtype=np.float32)
    scores = np.asarray([item[1] for item in candidates], dtype=np.float32)
    keep = nms(boxes, scores, iou_threshold=iou_threshold)

    detections: list[Detection] = []
    for index in keep:
        box, score, class_id = candidates[index]
        class_name = class_name_from_id(class_id)
        if class_name is None:
            continue
        detection = Detection(
            class_name=class_name,
            box=box,
            confidence=float(score),
        )
        detection.validate(width=width, height=height)
        detections.append(detection)
    return detections
