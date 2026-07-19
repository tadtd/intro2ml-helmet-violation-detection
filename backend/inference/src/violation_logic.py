from dataclasses import dataclass

from .models.base import Detection

Box = tuple[float, float, float, float]

# How far above a motorbike a rider's head can sit (in motorbike heights), and how
# far past its sides, when deciding whether a bare head belongs to that bike. The
# side margin is generous so every rider on a shared bike is grouped together.
RIDER_ZONE_ABOVE = 1.5
RIDER_SIDE_MARGIN = 0.25

def _center(box: Box) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2


def _area(box: Box) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _iou(a: Box, b: Box) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter == 0.0:
        return 0.0
    return inter / (_area(a) + _area(b) - inter)


def _containment(a: Box, b: Box) -> float:
    """Fraction of the smaller box covered by its overlap with the other."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    smaller = min(_area(a), _area(b))
    return inter / smaller if smaller > 0 else 0.0


def _suppress_duplicates(
    heads: list[Detection],
    iou_threshold: float = 0.5,
    containment_threshold: float = 0.7,
) -> list[Detection]:
    """Merge overlapping non-helmet boxes of the same rider within one frame.

    The detector often fires twice on one bare-head rider: a small head-only box
    and a larger whole-body box that contains it. Kept in confidence order, any box
    that overlaps or is largely inside an already-kept box is dropped, so one rider
    counts once instead of spawning a duplicate crop.
    """
    kept: list[Detection] = []
    for head in sorted(heads, key=lambda h: -h.confidence):
        if any(
            _iou(head.box, k.box) > iou_threshold
            or _containment(head.box, k.box) > containment_threshold
            for k in kept
        ):
            continue
        kept.append(head)
    return kept


def _expand_head(box: Box) -> Box:
    """Grow a bare-head box down and a little sideways to cover the whole rider."""
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    return (x1 - 0.4 * width, y1, x2 + 0.4 * width, y2 + 2.0 * height)


def _rider_score(motorbike: Detection, head: Detection) -> float:
    """How well a bare head fits as a rider of this motorbike; 0 means not a rider."""
    mx1, my1, mx2, my2 = motorbike.box
    mw = mx2 - mx1
    mh = my2 - my1
    head_cx, head_cy = _center(head.box)

    # The rider sits on/above the bike: head centre above the bike's bottom, over
    # the bike horizontally (with a side margin for passengers), and not floating
    # far above it (which would be someone standing behind, e.g. on a balcony).
    if head_cy > my2:
        return 0.0
    if not (mx1 - RIDER_SIDE_MARGIN * mw <= head_cx <= mx2 + RIDER_SIDE_MARGIN * mw):
        return 0.0
    if head_cy < my1 - RIDER_ZONE_ABOVE * mh:
        return 0.0

    bike_cx, bike_cy = _center(motorbike.box)
    distance = ((bike_cx - head_cx) ** 2 + (bike_cy - head_cy) ** 2) ** 0.5
    return 1.0 / (1.0 + distance)


@dataclass(frozen=True)
class Violation:
    # One violation per motorbike, holding every bare-head rider on it. The
    # motorbike is None only for bare heads that could not be tied to any bike.
    motorbike: Detection | None
    non_helmets: tuple[Detection, ...]

    @property
    def confidence(self) -> float:
        return max(head.confidence for head in self.non_helmets)

    def crop_box(self) -> Box:
        """Evidence region for this violation (clip to the frame at the call site).

        With a motorbike, it is the union of the bike and every rider on it. For a
        loose head (no bike), the head sits at the top of the rider, so extend it
        downward and a little sideways to include the body — a face-only crop is
        weak evidence.
        """
        if self.motorbike is not None:
            boxes = [self.motorbike.box] + [head.box for head in self.non_helmets]
            return (
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            )

        return _expand_head(self.non_helmets[0].box)

    def track_box(self) -> Box:
        """Stable box for cross-frame dedup: the primary (top-most) bare head
        expanded to the whole rider.

        Tracking this — never the motorbike — keeps a rider on one identity
        whether or not its bike is detected in a given frame, so it does not
        fragment into a new crop each time the bike box flickers. The box is large
        (the expanded head), which overlaps well between sampled frames even when
        the rider moves fast, so the same person stays one track.
        """
        head = min(self.non_helmets, key=lambda h: h.box[1]).box
        return _expand_head(head)


def find_violations(
    detections: list[Detection],
    min_confidence: float = 0.0,
) -> list[Violation]:
    """Group bare-head riders by the motorbike they ride.

    Each motorbike carrying at least one bare head becomes a single violation
    whose evidence crop covers the whole bike and everyone on it. Bare heads that
    do not sit on any detected motorbike each become their own violation.
    """
    motorbikes = [
        item
        for item in detections
        if item.class_name == "motorbike" and item.confidence >= min_confidence
    ]
    # Every non-helmet detection counts, even a head-only box: its crop is
    # expanded (loose) or unioned with the motorbike (grouped) to show the rider.
    # Overlapping duplicate boxes of the same rider are merged first.
    non_helmets = _suppress_duplicates(
        [
            item
            for item in detections
            if item.class_name == "non-helmet" and item.confidence >= min_confidence
        ]
    )

    groups: dict[int, list[Detection]] = {}
    loose: list[Detection] = []
    for head in non_helmets:
        best_index = None
        best_score = 0.0
        for index, motorbike in enumerate(motorbikes):
            score = _rider_score(motorbike, head)
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is None:
            loose.append(head)
        else:
            groups.setdefault(best_index, []).append(head)

    violations: list[Violation] = [
        Violation(motorbike=motorbikes[index], non_helmets=tuple(heads))
        for index, heads in groups.items()
    ]
    violations.extend(Violation(motorbike=None, non_helmets=(head,)) for head in loose)
    return violations
