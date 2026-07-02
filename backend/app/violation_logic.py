from dataclasses import dataclass

from .models.base import Detection
from .tracker import iou


@dataclass(frozen=True)
class Violation:
    motorbike: Detection
    non_helmet: Detection


def find_violations(
    detections: list[Detection],
    association_iou_threshold: float = 0.01,
) -> list[Violation]:
    motorbikes = [item for item in detections if item.class_name == "motorbike"]
    non_helmets = [item for item in detections if item.class_name == "non-helmet"]

    violations: list[Violation] = []
    for motorbike in motorbikes:
        linked = max(
            non_helmets,
            key=lambda item: iou(motorbike.box, item.box),
            default=None,
        )
        if linked and iou(motorbike.box, linked.box) >= association_iou_threshold:
            violations.append(Violation(motorbike=motorbike, non_helmet=linked))

    return violations
