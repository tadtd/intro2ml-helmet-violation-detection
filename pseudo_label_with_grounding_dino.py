import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

SOURCE_IMAGES_DIR = Path("dataset/images")
OUT_DIR = Path("data/pseudo_labels")
OUT_CSV = OUT_DIR / "pseudo_image_scores.csv"
OUT_DETECTIONS_JSON = OUT_DIR / "pseudo_instances_all.json"
OUT_NO_HELMET_JSON = OUT_DIR / "pseudo_instances_no_helmet.json"
REVIEW_DIR = Path("dataset/pseudo_review/no_helmet")

BATCH_SIZE_CPU = 1
BATCH_SIZE_GPU = 16

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
        "info": {"description": "Grounding DINO pseudo labels", "version": "1.0"},
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


def _load_checkpoint() -> set:
    """Trả về tập hợp source_path đã xử lý (để resume khi bị interrupt)."""
    if not OUT_CSV.exists():
        return set()
    done = set()
    try:
        with OUT_CSV.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done.add(row["source_path"])
    except Exception:
        pass
    return done


def run(args) -> None:
    """Run pseudo-labeling with a pre-parsed args namespace."""

    if not SOURCE_IMAGES_DIR.exists():
        raise FileNotFoundError(f"Missing source images directory: {SOURCE_IMAGES_DIR}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    image_paths = sorted([p for p in SOURCE_IMAGES_DIR.rglob("*") if p.is_file() and _is_image_file(p)])
    if not image_paths:
        raise ValueError(f"No images found in {SOURCE_IMAGES_DIR}")

    # Resume: bỏ qua ảnh đã xử lý
    done_paths = _load_checkpoint()
    remaining = [p for p in image_paths if str(p) not in done_paths]
    if done_paths:
        print(f"Resume: đã xử lý {len(done_paths)}, còn lại {len(remaining)}/{len(image_paths)}")
    else:
        _reset_dir(REVIEW_DIR)

    if not remaining:
        print("Tất cả ảnh đã được xử lý.")
        return

    print(f"Loading model: {args.model_id}")
    processor = AutoProcessor.from_pretrained(args.model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.model_id).to(args.device)
    model.eval()

    prompt_text = ". ".join(TEXT_QUERIES) + "."
    batch_size = BATCH_SIZE_GPU if args.device != "cpu" else BATCH_SIZE_CPU

    # Mở CSV theo chế độ append để checkpoint hoạt động
    csv_mode = "a" if done_paths else "w"
    csv_file = OUT_CSV.open(csv_mode, newline="", encoding="utf-8-sig")
    csv_fields = [
        "image_id", "file_name", "split", "source_path",
        "best_motorbike_score", "best_helmet_score", "best_no_helmet_score",
        "keep_no_helmet_candidate", "num_detections",
    ]
    writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
    if csv_mode == "w":
        writer.writeheader()

    # Dùng img_id tiếp theo sau checkpoint
    next_img_id = len(done_paths) + 1
    ann_id = 1
    coco_images: List[dict] = []
    coco_annotations: List[dict] = []
    coco_no_helmet_annotations: List[dict] = []
    total_processed = len(done_paths)
    total_kept = 0

    try:
        for batch_start in range(0, len(remaining), batch_size):
            batch_paths = remaining[batch_start: batch_start + batch_size]

            batch_images = [Image.open(p).convert("RGB") for p in batch_paths]
            batch_wh = [img.size for img in batch_images]  # (width, height)

            inputs = processor(
                images=batch_images,
                text=[prompt_text] * len(batch_images),
                return_tensors="pt",
                padding=True,
            )
            inputs = {k: v.to(args.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            target_sizes = [(h, w) for w, h in batch_wh]
            results = processor.post_process_grounded_object_detection(
                outputs,
                inputs["input_ids"],
                text_threshold=args.text_threshold,
                target_sizes=target_sizes,
            )

            for image_path, (width, height), result in zip(batch_paths, batch_wh, results):
                img_id = next_img_id
                next_img_id += 1

                raw_scores = result.get("scores", [])
                raw_boxes = result.get("boxes", [])
                raw_labels = result.get("text_labels", result.get("labels", []))

                detections: List[Detection] = []
                for box, score, label in zip(raw_boxes, raw_scores, raw_labels):
                    score_val = float(score.item())
                    if score_val < args.box_threshold:
                        continue
                    x1, y1, x2, y2 = [float(v) for v in box.tolist()]
                    w = max(0.0, x2 - x1)
                    h = max(0.0, y2 - y1)
                    if w <= 0 or h <= 0:
                        continue
                    cat_id, cat_name = _label_to_category(str(label))
                    if cat_id == 0:
                        continue
                    detections.append(Detection(cat_name, cat_id, score_val, [x1, y1, w, h]))

                best_no_helmet = _best_score(detections, "no_helmet")
                best_helmet = _best_score(detections, "helmet")
                best_motorbike = _best_score(detections, "motorbike")
                keep = (
                    best_no_helmet >= args.no_helmet_min_score
                    and best_motorbike >= args.motorbike_min_score
                    and best_no_helmet >= max(1e-9, best_helmet * args.no_helmet_vs_helmet_ratio)
                )

                split = _infer_split(image_path)

                if keep:
                    dst_dir = REVIEW_DIR / split
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(image_path, dst_dir / image_path.name)
                    total_kept += 1

                coco_images.append({
                    "id": img_id, "file_name": image_path.name,
                    "width": width, "height": height,
                    "split": split, "source_path": str(image_path),
                })

                for det in detections:
                    ann = {
                        "id": ann_id, "image_id": img_id,
                        "category_id": det.category_id,
                        "bbox": [round(v, 2) for v in det.bbox],
                        "area": round(det.bbox[2] * det.bbox[3], 2),
                        "iscrowd": 0, "segmentation": [],
                        "score": round(det.score, 4), "is_pseudo": 1,
                    }
                    coco_annotations.append(ann)
                    if det.category_name == "no_helmet":
                        coco_no_helmet_annotations.append(ann)
                    ann_id += 1

                writer.writerow({
                    "image_id": img_id,
                    "file_name": image_path.name,
                    "split": split,
                    "source_path": str(image_path),
                    "best_motorbike_score": round(best_motorbike, 4),
                    "best_helmet_score": round(best_helmet, 4),
                    "best_no_helmet_score": round(best_no_helmet, 4),
                    "keep_no_helmet_candidate": int(keep),
                    "num_detections": len(detections),
                })
                csv_file.flush()
                total_processed += 1

            # Progress mỗi batch
            pct = total_processed / len(image_paths) * 100
            print(f"[{total_processed}/{len(image_paths)}] {pct:.1f}%  no-helmet candidates: {total_kept}", end="\r")

    finally:
        csv_file.close()

    print(f"\nDone. Processed {total_processed} images, {total_kept} no-helmet candidates.")

    # Lưu COCO JSON (chỉ batch hiện tại — append vào file nếu cần full thì rebuild)
    _save_coco(OUT_DETECTIONS_JSON, coco_images, coco_annotations)
    _save_coco(OUT_NO_HELMET_JSON, coco_images, coco_no_helmet_annotations)
    print(f"CSV       : {OUT_CSV}")
    print(f"COCO all  : {OUT_DETECTIONS_JSON}")
    print(f"COCO no_helmet: {OUT_NO_HELMET_JSON}")
    print(f"Review    : {REVIEW_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pseudo-label dataset images with Grounding DINO")
    parser.add_argument("--model-id", default="IDEA-Research/grounding-dino-base")
    parser.add_argument("--box-threshold", type=float, default=0.28)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--no-helmet-min-score", type=float, default=0.40)
    parser.add_argument("--motorbike-min-score", type=float, default=0.30)
    parser.add_argument("--no-helmet-vs-helmet-ratio", type=float, default=1.05)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
