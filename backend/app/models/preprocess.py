from __future__ import annotations

import cv2
import numpy as np


def letterbox_bgr(
    image: np.ndarray,
    size: int = 640,
    color: tuple[int, int, int] = (114, 114, 114),
) -> tuple[np.ndarray, float, tuple[float, float]]:
    h, w = image.shape[:2]
    scale = min(size / h, size / w)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((size, size, 3), color, dtype=image.dtype)
    pad_x = (size - new_w) / 2
    pad_y = (size - new_h) / 2
    left = int(round(pad_x - 0.1))
    top = int(round(pad_y - 0.1))
    canvas[top:top + new_h, left:left + new_w] = resized
    return canvas, scale, (float(left), float(top))


def bgr_to_rgb_chw_tensor(image_bgr: np.ndarray) -> np.ndarray:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    image_rgb = image_rgb.astype(np.float32) / 255.0
    return np.transpose(image_rgb, (2, 0, 1))[None, ...]


def box_from_letterbox_to_original(
    box: tuple[float, float, float, float] | list[float] | np.ndarray,
    scale: float,
    pad: tuple[float, float],
) -> tuple[float, float, float, float]:
    pad_x, pad_y = pad
    x1, y1, x2, y2 = (float(value) for value in box)
    return (
        (x1 - pad_x) / scale,
        (y1 - pad_y) / scale,
        (x2 - pad_x) / scale,
        (y2 - pad_y) / scale,
    )


def resize_bgr_to_tensor(
    image: np.ndarray,
    size: int = 640,
) -> tuple[np.ndarray, float, float]:
    h, w = image.shape[:2]
    resized = cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
    return bgr_to_rgb_chw_tensor(resized), w / size, h / size
