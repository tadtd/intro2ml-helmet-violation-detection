"""Step 2 — Per-Class Specialist Model Training.

Trains one YOLOv8s single-class detector per class (motorbike, helmet, non-helmet).
Each specialist is trained ONLY on images that already have that class manually labeled,
using boxes for that class alone. This avoids relying on fully-labeled images, which
may be low quality in this dataset.

Prerequisite: run audit.py first.

Run:
    uv run python data_pipeline/bootstrap_train.py
"""

import json
import sys
from pathlib import Path

import yaml as _yaml
from pycocotools.coco import COCO
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dataset import build_specialist_yolo_dataset, write_dataset_yaml
from utils import get_paths, set_seed

SEED   = 42
MODEL  = "yolov8s.pt"
EPOCHS = 50
BATCH  = 16
IMGSZ  = 640

# COCO category id → specialist name
SPECIALISTS = {
    1: "motorbike",
    2: "helmet",
    3: "non-helmet",
}


def build_class_specialist_annotation(
    src_ann: Path,
    out_ann: Path,
    category_id: int,
    class_name: str,
) -> tuple[int, int]:
    """Build a single-class COCO JSON for one specialist model."""
    coco = COCO(str(src_ann))
    ann_ids = coco.getAnnIds(catIds=[category_id])
    anns = coco.loadAnns(ann_ids)
    image_ids = sorted({ann["image_id"] for ann in anns})
    images = [coco.imgs[iid] for iid in image_ids if iid in coco.imgs]

    specialist_anns = []
    for ann in anns:
        specialist_anns.append({
            "id": ann["id"],
            "image_id": ann["image_id"],
            "category_id": 1,  # single-class dataset
            "bbox": ann["bbox"],
            "area": ann["area"],
            "iscrowd": ann.get("iscrowd", 0),
        })

    subset = {
        "info": coco.dataset.get("info", {}),
        "licenses": coco.dataset.get("licenses", []),
        "categories": [{
            "id": 1,
            "name": class_name,
            "supercategory": "object",
        }],
        "images": images,
        "annotations": specialist_anns,
    }
    out_ann.write_text(json.dumps(subset))
    return len(images), len(specialist_anns)


def train_specialist(
    class_name: str,
    category_id: int,
    src_ann: Path,
    data_root: Path,
    out_root: Path,
    device: str,
) -> Path:
    """Train a single-class YOLO specialist and return checkpoint path."""
    ann_dir = data_root / "annotations"
    specialist_ann = ann_dir / f"instances_train_{class_name.replace('-', '_')}.json"
    n_images, n_anns = build_class_specialist_annotation(
        src_ann, specialist_ann, category_id, class_name
    )
    print(f"\n{class_name}: {n_images} images, {n_anns} boxes")

    if n_images == 0:
        print(f"  SKIP — no training images for {class_name}")
        return out_root / "specialists" / class_name.replace("-", "_") / "weights" / "best.pt"

    specialist_root = build_specialist_yolo_dataset(
        specialist_ann, data_root, class_name, seed=SEED, force=True
    )

    yaml_path = out_root / f"specialist_{class_name.replace('-', '_')}.yaml"
    write_dataset_yaml(
        yaml_path,
        specialist_root,
        nc=1,
        names=[class_name],
        test="images/val",
    )

    model = YOLO(MODEL)
    run_name = class_name.replace("-", "_")
    model.train(
        data=str(yaml_path),
        epochs=EPOCHS,
        batch=BATCH,
        imgsz=IMGSZ,
        device=device,
        seed=SEED,
        project=str(out_root / "specialists"),
        name=run_name,
        exist_ok=True,
        verbose=True,
    )

    ckpt = out_root / "specialists" / run_name / "weights" / "best.pt"
    print(f"  checkpoint → {ckpt}")
    return ckpt


def main() -> None:
    set_seed(SEED)
    data_root, out_root = get_paths()
    src_ann = data_root / "annotations" / "instances_train.json"

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    print("Training per-class specialist models (no fully-labeled subset) …")
    print(f"Device: {device}")

    manifest = {}
    for category_id, class_name in SPECIALISTS.items():
        ckpt = train_specialist(
            class_name, category_id, src_ann, data_root, out_root, device
        )
        manifest[class_name] = str(ckpt)

    manifest_path = out_root / "specialists" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nSpecialist manifest → {manifest_path}")


if __name__ == "__main__":
    main()
