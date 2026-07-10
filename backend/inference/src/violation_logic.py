from dataclasses import dataclass

from .models.base import Detection

Box = tuple[float, float, float, float]

# A rider sits above the motorbike, so the two boxes almost never overlap: measured
# on real footage, only ~4% of (head, nearest motorbike) pairs reach even a 0.01
# IoU. Associate against the space the rider occupies instead.
#
# The zone stays narrow horizontally on purpose. A pedestrian walking alongside a
# motorbike is the most common false positive, and the `non-helmet` class covers a
# rider's head and shoulders rather than just the head, so a generous sideways
# margin swallows bystanders.
RIDER_ZONE_ABOVE = 1.5  # extend upward by this many motorbike heights
RIDER_ZONE_HALF_WIDTH = 0.3  # half-width, as a fraction of the motorbike width


def _rider_zone(motorbike_box: Box) -> Box:
    """The region a rider's head and shoulders can occupy above a motorbike."""
    x1, y1, x2, y2 = motorbike_box
    width = x2 - x1
    height = y2 - y1
    centre_x = (x1 + x2) / 2
    return (
        # A rider straddles the bike, so their head stays near its centre line.
        centre_x - RIDER_ZONE_HALF_WIDTH * width,
        y1 - RIDER_ZONE_ABOVE * height,
        centre_x + RIDER_ZONE_HALF_WIDTH * width,
        # The head must sit above the middle of the bike, not beside it.
        y1 + 0.5 * height,
    )


def _center(box: Box) -> tuple[float, float]:
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2


def _contains(box: Box, point: tuple[float, float]) -> bool:
    x1, y1, x2, y2 = box
    x, y = point
    return x1 <= x <= x2 and y1 <= y <= y2


def _association_score(motorbike: Detection, head: Detection) -> float:
    """Higher is a better match. 0 means the head cannot belong to this motorbike."""
    if not _contains(_rider_zone(motorbike.box), _center(head.box)):
        return 0.0

    # Among the motorbikes whose rider zone covers this head, prefer the closest one.
    bike_x, bike_y = _center(motorbike.box)
    head_x, head_y = _center(head.box)
    distance = ((bike_x - head_x) ** 2 + (bike_y - head_y) ** 2) ** 0.5
    return 1.0 / (1.0 + distance)


@dataclass(frozen=True)
class Violation:
    motorbike: Detection
    non_helmet: Detection


def find_violations(
    detections: list[Detection],
    min_confidence: float = 0.5,
) -> list[Violation]:
    """Pair each bare head with the motorbike it is riding.

    A head is attributed to the motorbike whose rider zone contains the head's
    centre; when several qualify, the nearest one wins. Iterating over heads
    rather than motorbikes keeps one head from being reported twice when two
    bikes ride side by side.
    """
    # Low-confidence boxes are typically oversized and would stretch the rider
    # zone over half the frame, so drop them on both classes.
    motorbikes = [
        item
        for item in detections
        if item.class_name == "motorbike" and item.confidence >= min_confidence
    ]
    non_helmets = [
        item
        for item in detections
        if item.class_name == "non-helmet" and item.confidence >= min_confidence
    ]

    violations: list[Violation] = []
    for head in non_helmets:
        linked = max(
            motorbikes,
            key=lambda item: _association_score(item, head),
            default=None,
        )
        if linked is not None and _association_score(linked, head) > 0.0:
            violations.append(Violation(motorbike=linked, non_helmet=head))

    return violations
