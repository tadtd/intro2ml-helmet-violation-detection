from dataclasses import dataclass
from typing import Optional

from .models.base import Detection
from .tracker import centroid_distance, iou
import time

class ViolationWindow:
    def __init__(self, window_seconds: float = 30.0):
        self.last_saved: dict[int, float] = {}
        self.window = window_seconds

    def should_save(self, track_id: int) -> bool:
        now = time.time()
        last = self.last_saved.get(track_id)
        if last is None or (now - last) > self.window:
            self.last_saved[track_id] = now
            return True
        return False

@dataclass(frozen=True)
class Violation:
    track_id: int
    motorbike: Detection
    non_helmet: Detection


def find_violations(
    tracked_detections: list[Detection],
    distance_threshold: float = 200.0, # tune empirically based on resolution
) -> list[Violation]:
    motorbikes = [item for item in tracked_detections if item.class_name == "motorbike"]
    non_helmets = [item for item in tracked_detections if item.class_name == "non-helmet"]

    violations: list[Violation] = []
    
    for person in non_helmets:
        if person.track_id is None:
            continue
            
        nearest = min(
            motorbikes,
            key=lambda m: centroid_distance(person.box, m.box),
            default=None,
        )
        
        if nearest and centroid_distance(person.box, nearest.box) < distance_threshold:
            violations.append(Violation(
                track_id=person.track_id, 
                motorbike=nearest, 
                non_helmet=person
            ))

    return violations
