import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

SOURCE_IMAGES_DIR = Path("dataset/images")
OUT_DIR = Path("data/pseudo_labels")
OUT_CSV = OUT_DIR / "pseudo_image_scores.csv"
OUT_DETECTIONS_JSON = OUT_DIR / "pseudo_instances_all.json"
OUT_NO_HELMET_JSON = OUT_DIR / "pseudo_instances_no_helmet.json"
REVIEW_DIR = Path("dataset/pseudo_review/no_helmet")

TEXT_QUERIES = [
    "a motorcycle",
    "a motorbike rider",
    "a rider wearing a helmet",
    "a rider without a helmet",
    "a rider with no helmet",
]


@dataclass
class Detection:
    category_name: str
    category_id: int
    score: float
    bbox: List[float]


def _is_image_file(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}


def _infer_split(image_path: Path) -> str:
    parent = image_path.parent.name.lower()
    if parent in {"train", "val", "valid", "test"}:
        return "val" if parent == "valid" else parent
    return "unknown"


def _label_to_category(label: str) -> Tuple[int, str]:
    lower = label.lower()
    if "without a helmet" in lower or "with no helmet" in lower or "no helmet" in lower:
        return 3, "no_helmet"
    if "helmet" in lower:
        return 2, "helmet"
    if "motor" in lower or "bike" in lower or "rider" in lower or "scooter" in lower:
        return 1, "motorbike"
    return 0, "unknown"


def _best_score(dets: List[Detection], category_name: str) -> float:
    scores = [d.score for d in dets if d.category_name == category_name]
    return max(scores) if scores else 0.0


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _save_coco(path: Path, images: List[dict], annotations: List[dict]) -> None:
    data = {
        "info": {
            "description": "Grounding DINO pseudo labels",
            "version": "1.0",
        },
        "licenses": [],
        "images": images,
        "annotations": annotations,
        "categories": [
            {"id": 1, "name": "motorbike", "supercategory": "vehicle"},
            {"id": 2, "name": "helmet", "supercategory": "safety"},
            {"id": 3, "name": "no_helmet", "supercategory": "safety"},
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pseudo-label dataset images with Grounding DINO")
    parser.add_argument("--model-id", default="IDEA-Research/grounding-dino-base")
    parser.add_argument("--box-threshold", type=float, default=0.28)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--no-helmet-min-score", type=float, default=0.40)
    parser.add_argument("--motorbike-min-score", type=float, default=0.30)
    parser.add_argument("--no-helmet-vs-helmet-ratio", type=float, default=1.05)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    if not SOURCE_IMAGES_DIR.exists():
        raise FileNotFoundError(f"Missing source images directory: {SOURCE_IMAGES_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _reset_dir(REVIEW_DIR)

    image_paths = sorted([p for p in SOURCE_IMAGES_DIR.rglob("*") if p.is_file() and _is_image_file(p)])
    if not image_paths:
        raise ValueError(f"No images found in {SOURCE_IMAGES_DIR}")

    print(f"Loading model: {args.model_id}")
    processor = AutoProcessor.from_pretrained(args.model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.model_id).to(args.device)
    model.eval()

    prompt_text = ". ".join(TEXT_QUERIES) + "."

    image_rows = []
    coco_images = []
    coco_annotations = []
    coco_no_helmet_annotations = []

    ann_id = 1
    img_id = 1

    for image_path in image_paths:
        image = Image.open(image_path).convert("RGB")
        width, height = image.size

        inputs = processor(images=image, text=prompt_text, return_tensors="pt")
        inputs = {k: v.to(args.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        result = processor.post_process_grounded_object_detection(
            outputs,
            inputs["input_ids"],
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            target_sizes=[(height, width)],
        )[0]

        detections: List[Detection] = []
        boxes = result.get("boxes", [])
        scores = result.get("scores", [])
        labels = result.get("labels", [])

        for box, score, label in zip(boxes, scores, labels):
            score_val = float(score.item())
            box_xyxy = [float(v) for v in box.tolist()]
            x1, y1, x2, y2 = box_xyxy
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            if w <= 0 or h <= 0:
                continue

            cat_id, cat_name = _label_to_category(str(label))
            if cat_id == 0:
                continue

            detections.append(
                Detection(
                    category_name=cat_name,
                    category_id=cat_id,
                    score=score_val,
                    bbox=[x1, y1, w, h],
                )
            )

        best_no_helmet = _best_score(detections, "no_helmet")
        best_helmet = _best_score(detections, "helmet")
        best_motorbike = _best_score(detections, "motorbike")
        keep_no_helmet_candidate = (
            best_no_helmet >= args.no_helmet_min_score
            and best_motorbike >= args.motorbike_min_score
            and best_no_helmet >= max(1e-9, best_helmet * args.no_helmet_vs_helmet_ratio)
        )

        split = _infer_split(image_path)

        if keep_no_helmet_candidate:
            dst_dir = REVIEW_DIR / split
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_path, dst_dir / image_path.name)

        coco_images.append(
            {
                "id": img_id,
                "file_name": image_path.name,
                "width": width,
                "height": height,
                "split": split,
                "source_path": str(image_path),
            }
        )

        for det in detections:
            ann = {
                "id": ann_id,
                "image_id": img_id,
                "category_id": det.category_id,
                "bbox": [round(v, 2) for v in det.bbox],
                "area": round(det.bbox[2] * det.bbox[3], 2),
                "iscrowd": 0,
                "segmentation": [],
                "score": round(det.score, 4),
                "is_pseudo": 1,
            }
            coco_annotations.append(ann)
            if det.category_name == "no_helmet":
                coco_no_helmet_annotations.append(ann)
            ann_id += 1

        image_rows.append(
            {
                "image_id": img_id,
                "file_name": image_path.name,
                "split": split,
                "source_path": str(image_path),
                "best_motorbike_score": round(best_motorbike, 4),
                "best_helmet_score": round(best_helmet, 4),
                "best_no_helmet_score": round(best_no_helmet, 4),
                "keep_no_helmet_candidate": int(keep_no_helmet_candidate),
                "num_detections": len(detections),
            }
        )

        img_id += 1

    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image_id",
                "file_name",
                "split",
                "source_path",
                "best_motorbike_score",
                "best_helmet_score",
                "best_no_helmet_score",
                "keep_no_helmet_candidate",
                "num_detections",
            ],
        )
        writer.writeheader()
        writer.writerows(image_rows)

    _save_coco(OUT_DETECTIONS_JSON, coco_images, coco_annotations)
    _save_coco(OUT_NO_HELMET_JSON, coco_images, coco_no_helmet_annotations)

    kept = sum(r["keep_no_helmet_candidate"] for r in image_rows)
    print(f"Processed {len(image_rows)} images")
    print(f"No-helmet candidates: {kept}")
    print(f"CSV: {OUT_CSV}")
    print(f"Pseudo COCO (all): {OUT_DETECTIONS_JSON}")
    print(f"Pseudo COCO (no_helmet only): {OUT_NO_HELMET_JSON}")
    print(f"Review folder: {REVIEW_DIR}")


if __name__ == "__main__":
    main()
