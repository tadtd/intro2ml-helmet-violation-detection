from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

SPLITS = ("train", "val", "test")
PREFIX_PATTERN = re.compile(r"^(train|val|test)__([0-9]+)__(.+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge CVAT-corrected COCO annotations back into split COCO files."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data/processed/helmet_violation_coco"),
        help="Unified dataset root containing annotations and images.",
    )
    parser.add_argument(
        "--cvat-coco",
        type=Path,
        required=True,
        help="Path to CVAT-exported COCO JSON (with prefixed filenames).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Directory to store backup copies of current split annotation files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any annotation/image cannot be mapped.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def parse_prefixed_name(file_name: str) -> tuple[str, int, str] | None:
    base_name = Path(str(file_name)).name
    match = PREFIX_PATTERN.match(base_name)
    if not match:
        return None
    split = match.group(1)
    image_id = int(match.group(2))
    original_base_name = match.group(3)
    return split, image_id, original_base_name


def to_valid_bbox(
    bbox: Any,
    width: int,
    height: int,
) -> list[float] | None:
    if not isinstance(bbox, list) or len(bbox) < 4:
        return None

    try:
        x, y, w, h = map(float, bbox[:4])
    except (TypeError, ValueError):
        return None

    if width > 0 and height > 0:
        x = max(0.0, min(x, float(width - 1)))
        y = max(0.0, min(y, float(height - 1)))
        w = max(0.0, min(w, float(width) - x))
        h = max(0.0, min(h, float(height) - y))

    if w <= 1.0 or h <= 1.0:
        return None

    return [round(x, 3), round(y, 3), round(w, 3), round(h, 3)]


def backup_split_annotations(annotations_root: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        src = annotations_root / f"instances_{split}.json"
        dst = backup_dir / src.name
        shutil.copy2(src, dst)


def main() -> None:
    args = parse_args()

    dataset_root: Path = args.dataset_root
    annotations_root = dataset_root / "annotations"

    split_payloads: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        ann_path = annotations_root / f"instances_{split}.json"
        if not ann_path.exists():
            raise FileNotFoundError(f"Missing split annotation file: {ann_path}")
        split_payloads[split] = load_json(ann_path)

    cvat_payload = load_json(args.cvat_coco)

    # Categories are mapped by category name to preserve canonical IDs per split files.
    canonical_categories = split_payloads["train"].get("categories", [])
    canonical_category_id_by_name = {
        str(category.get("name")): int(category.get("id"))
        for category in canonical_categories
        if "name" in category and "id" in category
    }

    cvat_category_name_by_id = {
        int(category.get("id")): str(category.get("name"))
        for category in cvat_payload.get("categories", [])
        if "id" in category and "name" in category
    }

    image_lookup_by_split: dict[str, dict[int, dict[str, Any]]] = {}
    for split in SPLITS:
        image_lookup_by_split[split] = {
            int(image.get("id")): image for image in split_payloads[split].get("images", [])
        }

    cvat_image_ref: dict[int, tuple[str, int]] = {}

    stats = {
        "cvat_images": len(cvat_payload.get("images", [])),
        "cvat_annotations": len(cvat_payload.get("annotations", [])),
        "mapped_images": 0,
        "unmapped_images": 0,
        "mapped_annotations": 0,
        "skipped_unknown_image": 0,
        "skipped_unknown_category": 0,
        "skipped_invalid_bbox": 0,
    }

    for image in cvat_payload.get("images", []):
        cvat_image_id = int(image.get("id"))
        parsed = parse_prefixed_name(str(image.get("file_name", "")))
        if parsed is None:
            stats["unmapped_images"] += 1
            continue

        split, original_image_id, _ = parsed
        if original_image_id not in image_lookup_by_split[split]:
            stats["unmapped_images"] += 1
            continue

        cvat_image_ref[cvat_image_id] = (split, original_image_id)
        stats["mapped_images"] += 1

    merged_annotations_by_split: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "val": [],
        "test": [],
    }

    for annotation in cvat_payload.get("annotations", []):
        cvat_image_id = int(annotation.get("image_id"))
        if cvat_image_id not in cvat_image_ref:
            stats["skipped_unknown_image"] += 1
            continue

        split, original_image_id = cvat_image_ref[cvat_image_id]
        original_image = image_lookup_by_split[split][original_image_id]

        cvat_category_id = int(annotation.get("category_id"))
        category_name = cvat_category_name_by_id.get(cvat_category_id)
        target_category_id = canonical_category_id_by_name.get(category_name or "")
        if target_category_id is None:
            stats["skipped_unknown_category"] += 1
            continue

        width = int(original_image.get("width", 0) or 0)
        height = int(original_image.get("height", 0) or 0)
        bbox = to_valid_bbox(annotation.get("bbox"), width=width, height=height)
        if bbox is None:
            stats["skipped_invalid_bbox"] += 1
            continue

        merged_annotation = {
            "image_id": original_image_id,
            "category_id": target_category_id,
            "bbox": bbox,
            "area": round(bbox[2] * bbox[3], 3),
            "iscrowd": int(annotation.get("iscrowd", 0)),
        }
        if "segmentation" in annotation:
            merged_annotation["segmentation"] = annotation["segmentation"]

        merged_annotations_by_split[split].append(merged_annotation)
        stats["mapped_annotations"] += 1

    for split in SPLITS:
        for index, annotation in enumerate(merged_annotations_by_split[split], start=1):
            annotation["id"] = index

    if args.strict:
        error_count = (
            stats["unmapped_images"]
            + stats["skipped_unknown_image"]
            + stats["skipped_unknown_category"]
            + stats["skipped_invalid_bbox"]
        )
        if error_count > 0:
            raise SystemExit(
                "Strict mode failed due to unmapped/skipped records: "
                + json.dumps(stats, ensure_ascii=False)
            )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = (
        args.backup_dir
        if args.backup_dir is not None
        else annotations_root / f"backup_before_cvat_merge_{timestamp}"
    )
    backup_split_annotations(annotations_root=annotations_root, backup_dir=backup_dir)

    for split in SPLITS:
        payload = dict(split_payloads[split])
        payload["annotations"] = merged_annotations_by_split[split]
        output_path = annotations_root / f"instances_{split}.json"
        write_json(output_path, payload)

    report = {
        "dataset_root": str(dataset_root),
        "cvat_coco": str(args.cvat_coco),
        "backup_dir": str(backup_dir),
        "annotations_written": {
            split: len(merged_annotations_by_split[split]) for split in SPLITS
        },
        "stats": stats,
    }

    report_path = dataset_root / "reports" / "cvat_merge_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report_path, report)

    print("Merged CVAT annotations back into split files.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
