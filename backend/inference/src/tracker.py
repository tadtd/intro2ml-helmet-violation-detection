import math
from dataclasses import dataclass
from typing import Optional

from .models.base import Detection

@dataclass
class Track:
    track_id: int
    box: tuple[float, float, float, float]
    class_name: str
    confidence: float
    missed: int = 0

class IoUTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missed: int = 10) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self._next_id = 1
        self._tracks: list[Track] = []

    def update(self, detections: list[Detection]) -> list[Detection]:
        matched: set[int] = set()

        for track in self._tracks:
            best_index = -1
            best_iou = 0.0
            for index, det in enumerate(detections):
                if index in matched:
                    continue
                if det.class_name != track.class_name:
                    continue
                
                score = iou(track.box, det.box)
                if score > best_iou:
                    best_iou = score
                    best_index = index

            if best_index >= 0 and best_iou >= self.iou_threshold:
                track.box = detections[best_index].box
                track.confidence = detections[best_index].confidence
                track.missed = 0
                matched.add(best_index)
            else:
                track.missed += 1

        self._tracks = [
            track for track in self._tracks if track.missed <= self.max_missed
        ]

        for index, det in enumerate(detections):
            if index not in matched:
                self._tracks.append(Track(
                    track_id=self._next_id, 
                    box=det.box,
                    class_name=det.class_name,
                    confidence=det.confidence
                ))
                self._next_id += 1

        # Convert back to Detection objects with track_ids
        return [
            Detection(
                class_name=t.class_name, # type: ignore
                box=t.box,
                confidence=t.confidence,
                track_id=t.track_id
            )
            for t in self._tracks
        ]

    def reset(self):
        self._tracks.clear()
        self._next_id = 1

def iou(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if intersection == 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return intersection / (area_a + area_b - intersection)

def centroid_distance(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float]
) -> float:
    c_ax, c_ay = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    c_bx, c_by = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return math.sqrt((c_ax - c_bx)**2 + (c_ay - c_by)**2)
