"""Step 4 — Merge Manual + Pseudo Labels.

Combines the original instances_train.json (manual annotations) with
pseudo_labels.json (auto-generated annotations from Step 3).

Per image per class, runs NMS (IoU threshold = 0.5) to remove duplicate boxes.
Manual boxes always take priority over pseudo boxes on overlap.

Output: data/annotations/instances_train_merged.json

Prerequisite: run pseudo_label.py first.

Run:
    uv run python data_pipeline/merge_annotations.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from pycocotools.coco import COCO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import get_paths


def iou(box_a: list, box_b: list) -> float:
    """Compute IoU between two [x, y, w, h] boxes."""
    ax1, ay1, aw, ah = box_a
    bx1, by1, bw, bh = box_b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter == 0.0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def nms_with_priority(
    manual_boxes: list[dict],
    pseudo_boxes: list[dict],
    iou_thresh: float = 0.5,
) -> list[dict]:
    """NMS that keeps all manual boxes and removes pseudo boxes that overlap them.

    Among remaining pseudo boxes, also removes duplicates by standard NMS
    (highest score wins).
    """
    kept = list(manual_boxes)

    for pseudo in pseudo_boxes:
        overlaps_manual = any(
            iou(pseudo["bbox"], m["bbox"]) >= iou_thresh for m in manual_boxes
        )
        if not overlaps_manual:
            kept.append(pseudo)

    # Deduplicate remaining pseudo-pseudo overlaps (score-ordered NMS)
    pseudo_only = [a for a in kept if a not in manual_boxes]
    pseudo_only.sort(key=lambda a: a.get("score", 0.0), reverse=True)

    final_pseudo: list[dict] = []
    for ann in pseudo_only:
        suppressed = any(
            iou(ann["bbox"], kept_ann["bbox"]) >= iou_thresh
            for kept_ann in final_pseudo
        )
        if not suppressed:
            final_pseudo.append(ann)

    return list(manual_boxes) + final_pseudo


def main() -> None:
    data_root, out_root = get_paths()

    src_ann    = data_root / "annotations" / "instances_train.json"
    pseudo_ann = data_root / "annotations" / "pseudo_labels.json"

    if not pseudo_ann.exists():
        print(f"ERROR: {pseudo_ann} not found. Run pseudo_label.py first.")
        sys.exit(1)

    coco = COCO(str(src_ann))
    pseudo_annotations: list[dict] = json.loads(pseudo_ann.read_text())

    print(f"Manual annotations  : {len(coco.dataset['annotations']):,}")
    print(f"Pseudo annotations  : {len(pseudo_annotations):,}")

    # Group manual annotations by (image_id, category_id)
    manual_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for ann in coco.dataset["annotations"]:
        manual_by_key[(ann["image_id"], ann["category_id"])].append(ann)

    # Group pseudo annotations by (image_id, category_id)
    pseudo_by_key: dict[tuple, list[dict]] = defaultdict(list)
    for ann in pseudo_annotations:
        pseudo_by_key[(ann["image_id"], ann["category_id"])].append(ann)

    # Merge per (image_id, category_id)
    merged: list[dict] = []
    for key in set(list(manual_by_key.keys()) + list(pseudo_by_key.keys())):
        manual = manual_by_key.get(key, [])
        pseudo = pseudo_by_key.get(key, [])
        kept = nms_with_priority(manual, pseudo)
        merged.extend(kept)

    # Assign new sequential IDs
    for new_id, ann in enumerate(merged, start=1):
        ann["id"] = new_id
        ann.pop("score", None)  # remove internal score field from final output

    # Build output JSON (same structure as instances_train.json)
    output = {
        "info":        coco.dataset.get("info", {}),
        "licenses":    coco.dataset.get("licenses", []),
        "categories":  coco.dataset["categories"],
        "images":      coco.dataset["images"],
        "annotations": merged,
    }

    out_path = data_root / "annotations" / "instances_train_merged.json"
    out_path.write_text(json.dumps(output))

    n_added   = len(merged) - len(coco.dataset["annotations"])
    n_removed = len(pseudo_annotations) - max(0, n_added)

    print(f"\nMerge complete:")
    print(f"  Manual annotations  : {len(coco.dataset['annotations']):,}")
    print(f"  Pseudo annotations  : {len(pseudo_annotations):,}")
    print(f"  Removed by NMS      : {max(0, len(pseudo_annotations) - n_added):,}")
    print(f"  Final annotations   : {len(merged):,}")
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
