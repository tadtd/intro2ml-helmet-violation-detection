from dataclasses import dataclass


@dataclass
class Track:
    track_id: int
    box: tuple[float, float, float, float]
    missed: int = 0


class IoUTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missed: int = 10) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self._next_id = 1
        self._tracks: list[Track] = []

    def update(self, boxes: list[tuple[float, float, float, float]]) -> list[Track]:
        matched: set[int] = set()

        for track in self._tracks:
            best_index = -1
            best_iou = 0.0
            for index, box in enumerate(boxes):
                if index in matched:
                    continue
                score = iou(track.box, box)
                if score > best_iou:
                    best_iou = score
                    best_index = index

            if best_index >= 0 and best_iou >= self.iou_threshold:
                track.box = boxes[best_index]
                track.missed = 0
                matched.add(best_index)
            else:
                track.missed += 1

        self._tracks = [
            track for track in self._tracks if track.missed <= self.max_missed
        ]

        for index, box in enumerate(boxes):
            if index not in matched:
                self._tracks.append(Track(track_id=self._next_id, box=box))
                self._next_id += 1

        return list(self._tracks)


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
