from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPLITS = ("train", "val", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a single COCO task bundle for CVAT from split COCO files."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("data/processed/helmet_violation_coco"),
        help="Unified dataset root containing images/ and annotations/.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed/cvat_round1"),
        help="Output directory for the CVAT-ready bundle.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=list(SPLITS),
        choices=list(SPLITS),
        help="Dataset splits to include in the CVAT task.",
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Skip creating cvat_upload_bundle.zip.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output directory if it already exists.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def build_prefixed_name(split: str, image_id: int, file_name: str) -> str:
    # Prefix split and original image id so the CVAT export can be mapped back exactly.
    base_name = Path(str(file_name)).name
    return f"{split}__{image_id}__{base_name}"


def prepare_bundle(dataset_root: Path, output_root: Path, splits: list[str]) -> dict[str, Any]:
    annotations_root = dataset_root / "annotations"
    images_root = dataset_root / "images"

    for split in splits:
        ann_path = annotations_root / f"instances_{split}.json"
        image_split_dir = images_root / split
        if not ann_path.exists():
            raise FileNotFoundError(f"Missing annotation file: {ann_path}")
        if not image_split_dir.exists():
            raise FileNotFoundError(f"Missing image directory: {image_split_dir}")

    out_images = output_root / "images"
    out_annotations = output_root / "annotations"
    out_reports = output_root / "reports"
    out_images.mkdir(parents=True, exist_ok=True)
    out_annotations.mkdir(parents=True, exist_ok=True)
    out_reports.mkdir(parents=True, exist_ok=True)

    combined_images: list[dict[str, Any]] = []
    combined_annotations: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []

    categories: list[dict[str, Any]] | None = None
    next_image_id = 1
    next_ann_id = 1
    skipped_missing_images = 0
    skipped_orphan_annotations = 0

    split_image_id_map: dict[tuple[str, int], int] = {}

    for split in splits:
        split_coco = load_json(annotations_root / f"instances_{split}.json")
        if categories is None:
            categories = split_coco.get("categories", [])

        split_images = split_coco.get("images", [])
        split_annotations = split_coco.get("annotations", [])

        for image in split_images:
            original_image_id = int(image.get("id"))
            original_file_name = str(image.get("file_name", ""))
            if not original_file_name:
                continue

            src_path = images_root / split / original_file_name
            if not src_path.exists():
                skipped_missing_images += 1
                continue

            prefixed_file_name = build_prefixed_name(split, original_image_id, original_file_name)
            dst_path = out_images / prefixed_file_name
            shutil.copy2(src_path, dst_path)

            width = int(image.get("width", 0) or 0)
            height = int(image.get("height", 0) or 0)

            combined_images.append(
                {
                    "id": next_image_id,
                    "file_name": prefixed_file_name,
                    "width": width,
                    "height": height,
                    "source_split": split,
                    "orig_image_id": original_image_id,
                    "orig_file_name": original_file_name,
                }
            )
            split_image_id_map[(split, original_image_id)] = next_image_id

            mapping_rows.append(
                {
                    "split": split,
                    "orig_image_id": original_image_id,
                    "orig_file_name": original_file_name,
                    "prefixed_file_name": prefixed_file_name,
                    "width": width,
                    "height": height,
                }
            )
            next_image_id += 1

        for annotation in split_annotations:
            orig_image_id = int(annotation.get("image_id"))
            key = (split, orig_image_id)
            if key not in split_image_id_map:
                skipped_orphan_annotations += 1
                continue

            merged_annotation = dict(annotation)
            merged_annotation["id"] = next_ann_id
            merged_annotation["image_id"] = split_image_id_map[key]
            if "area" not in merged_annotation:
                bbox = merged_annotation.get("bbox", [])
                if isinstance(bbox, list) and len(bbox) >= 4:
                    merged_annotation["area"] = float(bbox[2]) * float(bbox[3])
            combined_annotations.append(merged_annotation)
            next_ann_id += 1

    payload = {
        "info": {
            "description": "CVAT review task generated from helmet_violation_coco",
            "version": "1.0",
            "date_created": datetime.now(timezone.utc).isoformat(),
            "included_splits": splits,
        },
        "licenses": [],
        "categories": categories or [],
        "images": combined_images,
        "annotations": combined_annotations,
    }

    coco_path = out_annotations / "instances_all_for_cvat.json"
    write_json(coco_path, payload)

    mapping_path = out_reports / "image_mapping.csv"
    with mapping_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "split",
                "orig_image_id",
                "orig_file_name",
                "prefixed_file_name",
                "width",
                "height",
            ],
        )
        writer.writeheader()
        writer.writerows(mapping_rows)

    summary = {
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "splits": splits,
        "images": len(combined_images),
        "annotations": len(combined_annotations),
        "skipped_missing_images": skipped_missing_images,
        "skipped_orphan_annotations": skipped_orphan_annotations,
        "coco_path": str(coco_path),
        "mapping_path": str(mapping_path),
    }
    write_json(out_reports / "prepare_summary.json", summary)
    return summary


def maybe_make_zip(output_root: Path) -> Path:
    archive_base = output_root / "cvat_upload_bundle"
    zip_path = Path(f"{archive_base}.zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(archive_base), "zip", root_dir=output_root)
    return zip_path


def main() -> None:
    args = parse_args()

    dataset_root: Path = args.dataset_root
    output_root: Path = args.output_root
    splits: list[str] = list(dict.fromkeys(args.splits))

    if output_root.exists():
        if args.overwrite:
            shutil.rmtree(output_root)
        else:
            raise FileExistsError(
                f"Output directory already exists: {output_root}. Use --overwrite to replace it."
            )

    summary = prepare_bundle(dataset_root=dataset_root, output_root=output_root, splits=splits)

    zip_path: str | None = None
    if not args.skip_zip:
        zip_path = str(maybe_make_zip(output_root))

    report = dict(summary)
    report["zip_path"] = zip_path

    print("CVAT bundle prepared successfully.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
