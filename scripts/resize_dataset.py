"""
Resize helmet_violation_coco dataset to a fixed square size using letterbox padding.

Letterbox: scale image to fit within target_size x target_size while preserving
aspect ratio, then pad the remaining space with gray (128, 128, 128).

BBox coordinates in COCO annotations are updated accordingly.

Usage:
    python scripts/resize_dataset.py \
        --dataset-root helmet_violation_coco \
        --output-root helmet_violation_coco_640 \
        --size 640

    # Or 1280 for better small-object detection (needs more VRAM):
    python scripts/resize_dataset.py \
        --dataset-root helmet_violation_coco \
        --output-root helmet_violation_coco_1280 \
        --size 1280
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SPLITS = ("train", "val", "test")
PAD_COLOR = (114, 114, 114)  # standard gray used by YOLOv5/v8


# ---------------------------------------------------------------------------
# Letterbox helpers
# ---------------------------------------------------------------------------

@dataclass
class LetterboxParams:
    scale: float
    pad_left: int
    pad_top: int
    new_w: int   # image width after scale, before pad
    new_h: int   # image height after scale, before pad


def compute_letterbox(src_w: int, src_h: int, target: int) -> LetterboxParams:
    scale = min(target / src_w, target / src_h)
    new_w = round(src_w * scale)
    new_h = round(src_h * scale)
    pad_left = (target - new_w) // 2
    pad_top = (target - new_h) // 2
    return LetterboxParams(scale=scale, pad_left=pad_left, pad_top=pad_top,
                           new_w=new_w, new_h=new_h)


def letterbox_image(img: Image.Image, target: int) -> tuple[Image.Image, LetterboxParams]:
    src_w, src_h = img.size
    lb = compute_letterbox(src_w, src_h, target)
    resized = img.resize((lb.new_w, lb.new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target, target), PAD_COLOR)
    canvas.paste(resized, (lb.pad_left, lb.pad_top))
    return canvas, lb


def transform_bbox(bbox: list[float], lb: LetterboxParams) -> list[float]:
    """Transform COCO bbox [x, y, w, h] using letterbox params."""
    x, y, w, h = bbox
    x_new = x * lb.scale + lb.pad_left
    y_new = y * lb.scale + lb.pad_top
    w_new = w * lb.scale
    h_new = h * lb.scale
    return [round(x_new, 2), round(y_new, 2), round(w_new, 2), round(h_new, 2)]


# ---------------------------------------------------------------------------
# Per-split processing
# ---------------------------------------------------------------------------

def process_split(
    split: str,
    src_img_dir: Path,
    src_ann_path: Path,
    dst_img_dir: Path,
    dst_ann_path: Path,
    target: int,
) -> dict:
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_ann_path.parent.mkdir(parents=True, exist_ok=True)

    with open(src_ann_path) as f:
        coco = json.load(f)

    # Build letterbox params per image (keyed by image id)
    lb_map: dict[int, LetterboxParams] = {}
    new_images = []

    skipped = 0
    processed = 0
    already_target = 0

    total = len(coco["images"])
    print(f"  [{split}] Processing {total} images ...", flush=True)

    for i, img_meta in enumerate(coco["images"], 1):
        src_path = src_img_dir / img_meta["file_name"]
        dst_path = dst_img_dir / img_meta["file_name"]

        if not src_path.exists():
            print(f"    WARNING: missing {src_path.name} — skipping")
            skipped += 1
            continue

        src_w, src_h = img_meta["width"], img_meta["height"]

        if src_w == target and src_h == target:
            # Already target size — copy as-is, lb is identity
            shutil.copy2(src_path, dst_path)
            lb = LetterboxParams(scale=1.0, pad_left=0, pad_top=0,
                                 new_w=target, new_h=target)
            already_target += 1
        else:
            img = Image.open(src_path).convert("RGB")
            canvas, lb = letterbox_image(img, target)
            canvas.save(dst_path, quality=95, subsampling=0)
            processed += 1

        lb_map[img_meta["id"]] = lb

        updated_meta = copy.copy(img_meta)
        updated_meta["width"] = target
        updated_meta["height"] = target
        updated_meta["letterbox_scale"] = round(lb.scale, 6)
        updated_meta["letterbox_pad_left"] = lb.pad_left
        updated_meta["letterbox_pad_top"] = lb.pad_top
        updated_meta["orig_width"] = src_w
        updated_meta["orig_height"] = src_h
        new_images.append(updated_meta)

        if i % 500 == 0:
            print(f"    {i}/{total} done", flush=True)

    # Update annotations
    new_annotations = []
    ann_skipped = 0
    for ann in coco["annotations"]:
        if ann["image_id"] not in lb_map:
            ann_skipped += 1
            continue
        lb = lb_map[ann["image_id"]]
        new_ann = copy.copy(ann)
        new_ann["bbox"] = transform_bbox(ann["bbox"], lb)
        x, y, w, h = new_ann["bbox"]
        new_ann["area"] = round(w * h, 2)
        new_annotations.append(new_ann)

    new_coco = copy.copy(coco)
    new_coco["images"] = new_images
    new_coco["annotations"] = new_annotations
    new_coco["info"] = copy.copy(coco.get("info", {}))
    new_coco["info"]["target_size"] = f"{target}x{target}"
    new_coco["info"]["letterbox_pad_color"] = list(PAD_COLOR)

    with open(dst_ann_path, "w") as f:
        json.dump(new_coco, f, indent=2)

    stats = {
        "total": total,
        "processed": processed,
        "already_target_size": already_target,
        "skipped_missing": skipped,
        "annotations_kept": len(new_annotations),
        "annotations_skipped": ann_skipped,
    }
    print(f"  [{split}] Done — resized: {processed}, already {target}px: {already_target}, "
          f"skipped: {skipped}", flush=True)
    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Letterbox-resize helmet_violation_coco dataset")
    parser.add_argument("--dataset-root", default="helmet_violation_coco",
                        help="Path to the source dataset (default: helmet_violation_coco)")
    parser.add_argument("--output-root", default=None,
                        help="Output directory (default: helmet_violation_coco_<size>)")
    parser.add_argument("--size", type=int, default=640,
                        help="Target square size in pixels (default: 640)")
    args = parser.parse_args()

    src_root = Path(args.dataset_root)
    target = args.size
    dst_root = Path(args.output_root) if args.output_root else Path(f"helmet_violation_coco_{target}")

    print(f"Source      : {src_root}")
    print(f"Destination : {dst_root}")
    print(f"Target size : {target}x{target}")
    print(f"Filter      : PIL LANCZOS")
    print(f"Pad color   : RGB{PAD_COLOR}")
    print()

    t0 = time.perf_counter()
    report = {"target_size": target, "pad_color": list(PAD_COLOR), "splits": {}}

    for split in SPLITS:
        src_img_dir = src_root / "images" / split
        src_ann = src_root / "annotations" / f"instances_{split}.json"
        dst_img_dir = dst_root / "images" / split
        dst_ann = dst_root / "annotations" / f"instances_{split}.json"

        if not src_ann.exists():
            print(f"  [{split}] annotation file not found — skipping\n")
            continue
        if not src_img_dir.exists():
            print(f"  [{split}] image directory not found — skipping\n")
            continue

        stats = process_split(split, src_img_dir, src_ann, dst_img_dir, dst_ann, target)
        report["splits"][split] = stats

    elapsed = time.perf_counter() - t0
    report["elapsed_seconds"] = round(elapsed, 1)

    report_dir = dst_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "resize_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print()
    print(f"Finished in {elapsed:.1f}s")
    print(f"Report saved to {report_path}")
    print(f"Output dataset at: {dst_root}/")


if __name__ == "__main__":
    main()
