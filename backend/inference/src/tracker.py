from dataclasses import dataclass

Box = tuple[float, float, float, float]


def _center(box: Box) -> tuple[float, float]:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


def _diag(box: Box) -> float:
    return ((box[2] - box[0]) ** 2 + (box[3] - box[1]) ** 2) ** 0.5


def _area(box: Box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _shift(box: Box, dx: float, dy: float) -> Box:
    return (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)


@dataclass
class Track:
    track_id: int
    box: Box
    vx: float = 0.0
    vy: float = 0.0
    missed: int = 0


class IoUTracker:
    """Associates boxes across sampled frames into stable tracks.

    Matching is done against each track's *predicted* next box (its last box
    shifted by the recent velocity), not its last box. A rider moving fast enough
    that its new detection barely overlaps the previous frame still lands on the
    predicted box, so it keeps one id instead of fragmenting into a fresh track
    (and a duplicate crop) every frame. A tight, size-gated centre-distance pass
    then catches the very first move, before any velocity is known, without ever
    linking two boxes that are far apart or clearly different in scale — so two
    distinct riders passing the same spot never merge into one.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_missed: int = 10,
        center_gate: float = 0.5,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self.center_gate = center_gate
        self._next_id = 1
        self._tracks: list[Track] = []

    def _predicted(self, track: Track) -> Box:
        return _shift(track.box, track.vx, track.vy)

    def _absorb(self, track: Track, box: Box) -> None:
        ocx, ocy = _center(track.box)
        ncx, ncy = _center(box)
        # Exponential smoothing keeps velocity responsive but steady against jitter.
        track.vx = 0.3 * track.vx + 0.7 * (ncx - ocx)
        track.vy = 0.3 * track.vy + 0.7 * (ncy - ocy)
        track.box = box
        track.missed = 0

    def update(self, boxes: list[Box]) -> list[Track]:
        matched: set[int] = set()

        # Pass 1: overlap match against each track's predicted next box.
        for track in self._tracks:
            predicted = self._predicted(track)
            best_index, best_iou = -1, 0.0
            for index, box in enumerate(boxes):
                if index in matched:
                    continue
                score = iou(predicted, box)
                if score > best_iou:
                    best_iou, best_index = score, index
            if best_index >= 0 and best_iou >= self.iou_threshold:
                self._absorb(track, boxes[best_index])
                matched.add(best_index)
            else:
                track.missed += 1

        # Pass 2: rescue a fast mover that overlaps nothing this frame by linking it
        # to a still-unmatched track when the new box is close to the prediction and
        # a similar size. The size and distance gates keep distinct riders apart.
        for track in self._tracks:
            if track.missed == 0:
                continue
            pcx, pcy = _center(self._predicted(track))
            best_index, best_dist = -1, None
            for index, box in enumerate(boxes):
                if index in matched:
                    continue
                ratio = _area(box) / (_area(track.box) + 1e-6)
                if not (0.6 <= ratio <= 1.7):
                    continue
                bcx, bcy = _center(box)
                dist = ((pcx - bcx) ** 2 + (pcy - bcy) ** 2) ** 0.5
                gate = self.center_gate * (_diag(track.box) + _diag(box)) / 2.0
                if dist <= gate and (best_dist is None or dist < best_dist):
                    best_dist, best_index = dist, index
            if best_index >= 0:
                self._absorb(track, boxes[best_index])
                matched.add(best_index)

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
