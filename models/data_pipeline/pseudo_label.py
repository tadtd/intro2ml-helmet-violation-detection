"""Step 3 — Pseudo-Label Generation (Per-Class Specialists).

For each partial image, runs the specialist model for each missing class and keeps
predictions with score >= CONF_THRESHOLD. Each specialist is a single-class detector
trained on images where that class was manually labeled.

Prerequisite: run audit.py and bootstrap_train.py (specialist training) first.

Run:
    uv run python data_pipeline/pseudo_label.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
from pycocotools.coco import COCO
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import get_paths

CONF_THRESHOLD = 0.4
CAT_NAME_TO_ID = {"motorbike": 1, "helmet": 2, "non-helmet": 3}


def specialist_ckpt(out_root: Path, class_name: str) -> Path:
    return out_root / "specialists" / class_name.replace("-", "_") / "weights" / "best.pt"


def load_specialists(out_root: Path) -> dict[str, YOLO]:
    manifest_path = out_root / "specialists" / "manifest.json"
    models: dict[str, YOLO] = {}

    if manifest_path.exists():
        manifest: dict[str, str] = json.loads(manifest_path.read_text())
        for class_name, ckpt_str in manifest.items():
            ckpt = Path(ckpt_str)
            if ckpt.exists():
                models[class_name] = YOLO(str(ckpt))
        return models

    # Fallback if manifest missing
    for class_name in CAT_NAME_TO_ID:
        ckpt = specialist_ckpt(out_root, class_name)
        if ckpt.exists():
            models[class_name] = YOLO(str(ckpt))
    return models


def main() -> None:
    data_root, out_root = get_paths()

    missing_file = out_root / "audit" / "missing_per_image.json"
    if not missing_file.exists():
        print("ERROR: audit/missing_per_image.json not found. Run audit.py first.")
        sys.exit(1)

    missing_per_image: dict[str, list[str]] = json.loads(missing_file.read_text())
    if not missing_per_image:
        print("No partial images — pseudo-labeling not needed.")
        sys.exit(0)

    specialists = load_specialists(out_root)
    if not specialists:
        print("ERROR: No specialist checkpoints found. Run bootstrap_train.py first.")
        sys.exit(1)

    img_dir = data_root / "images" / "train"
    src_ann = data_root / "annotations" / "instances_train.json"
    coco = COCO(str(src_ann))

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    print(f"Device: {device}")
    print(f"Loaded specialists: {', '.join(specialists.keys())}")
    print(f"Pseudo-labeling {len(missing_per_image)} partial images …")

    pseudo_annotations = []
    score_log = []
    ann_id = 1_000_000

    img_ids = [int(k) for k in missing_per_image]
    total = len(img_ids)

    for idx, img_id in enumerate(img_ids, 1):
        if img_id not in coco.imgs:
            continue
        img_info = coco.imgs[img_id]
        missing_classes = missing_per_image[str(img_id)]

        img_path = img_dir / img_info["file_name"]
        if not img_path.exists():
            continue

        if idx % 100 == 0 or idx == total:
            print(f"  {idx}/{total}", flush=True)

        for class_name in missing_classes:
            model = specialists.get(class_name)
            if model is None:
                continue

            cat_id = CAT_NAME_TO_ID[class_name]
            results = model.predict(
                str(img_path),
                device=device,
                verbose=False,
                conf=CONF_THRESHOLD,
            )

            for result in results:
                if result.boxes is None:
                    continue
                boxes = result.boxes.xywh.cpu().tolist()
                scores = result.boxes.conf.cpu().tolist()

                for (cx, cy, bw, bh), score in zip(boxes, scores):
                    if score < CONF_THRESHOLD:
                        continue

                    x = cx - bw / 2
                    y = cy - bh / 2

                    pseudo_annotations.append({
                        "id": ann_id,
                        "image_id": img_id,
                        "category_id": cat_id,
                        "bbox": [round(x, 2), round(y, 2), round(bw, 2), round(bh, 2)],
                        "area": round(bw * bh, 2),
                        "iscrowd": 0,
                        "score": round(float(score), 4),
                    })
                    score_log.append({
                        "image_id": img_id,
                        "ann_id": ann_id,
                        "category_id": cat_id,
                        "class_name": class_name,
                        "score": round(float(score), 4),
                        "bbox": [round(x, 2), round(y, 2), round(bw, 2), round(bh, 2)],
                    })
                    ann_id += 1

    pseudo_out = data_root / "annotations" / "pseudo_labels.json"
    pseudo_out.write_text(json.dumps(pseudo_annotations))

    audit_dir = out_root / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(score_log).to_csv(audit_dir / "pseudo_label_scores.csv", index=False)

    n_high = sum(1 for r in score_log if r["score"] >= 0.6)
    n_medium = sum(1 for r in score_log if 0.4 <= r["score"] < 0.6)

    print(f"\nPseudo-labels generated: {len(pseudo_annotations)}")
    print(f"  High confidence  (>=0.6)   : {n_high:,}")
    print(f"  Medium confidence (0.4-0.6): {n_medium:,}")
    print(f"\nSaved → {pseudo_out}")
    print(f"Score log → {audit_dir / 'pseudo_label_scores.csv'}")


if __name__ == "__main__":
    main()
