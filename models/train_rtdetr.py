"""RT-DETR-L training script.

Run locally:
    uv run python train_rtdetr.py

Run on Kaggle (from repo root):
    uv run python train/train_rtdetr.py
"""

import json
import sys
from pathlib import Path

import torch
from ultralytics import RTDETR

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset import coco_to_yolo_labels, write_dataset_yaml
from metrics import measure_fps
from utils import get_paths, set_seed

# ── Config ────────────────────────────────────────────────────────────────────
SEED         = 42
MODEL        = "rtdetr-l.pt"
EPOCHS       = 50
BATCH        = 8
IMGSZ        = 640
LR0          = 1e-4
LRF          = 0.01
MOMENTUM     = 0.937
WEIGHT_DECAY = 5e-4
NC           = 3
NAMES        = ["motorbike", "helmet", "non-helmet"]
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    set_seed(SEED)
    data_root, out_root = get_paths()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Data:   {data_root}")
    print(f"Output: {out_root}")

    ann_dir = data_root / "annotations"

    merged = ann_dir / "instances_train_merged.json"
    train_ann = merged if merged.exists() else ann_dir / "instances_train.json"
    print(f"Train annotations: {train_ann.name}")

    print("\nConverting COCO annotations to YOLO label format …")
    for split, ann_file in [
        ("train", train_ann),
        ("val",   ann_dir / "instances_val.json"),
        ("test",  ann_dir / "instances_test.json"),
    ]:
        coco_to_yolo_labels(ann_file, data_root, split)

    yaml_path = out_root / "dataset.yaml"
    write_dataset_yaml(yaml_path, data_root, NC, NAMES)
    print(f"Dataset YAML → {yaml_path}")

    print(f"\nTraining {MODEL} for {EPOCHS} epochs …")
    model = RTDETR(MODEL)
    model.train(
        data=str(yaml_path),
        epochs=EPOCHS,
        batch=BATCH,
        imgsz=IMGSZ,
        lr0=LR0,
        lrf=LRF,
        momentum=MOMENTUM,
        weight_decay=WEIGHT_DECAY,
        device=device,
        seed=SEED,
        project=str(out_root),
        name="rtdetr_train",
        exist_ok=True,
        verbose=True,
    )

    best_pt = out_root / "rtdetr_train" / "weights" / "best.pt"
    dest_pt = out_root / "rtdetr_best.pt"
    if best_pt.exists():
        import shutil
        shutil.copy(best_pt, dest_pt)
        print(f"\nBest weights → {dest_pt}")

    print("\nEvaluating on val split …")
    val_results  = model.val(data=str(yaml_path), split="val",  device=device, verbose=False)
    print("Evaluating on test split …")
    test_results = model.val(data=str(yaml_path), split="test", device=device, verbose=False)

    def extract_metrics(r) -> dict:
        return {
            "mAP50":    float(r.box.map50),
            "mAP50_95": float(r.box.map),
            "AR100":    float(r.box.mr),
        }

    val_metrics  = extract_metrics(val_results)
    test_metrics = extract_metrics(test_results)

    best_model = RTDETR(str(dest_pt))
    dummy_input = torch.zeros(1, 3, IMGSZ, IMGSZ)
    fps = measure_fps(
        lambda x: best_model.predict(x, verbose=False),
        dummy_input,
    )

    results = {"val": val_metrics, "test": test_metrics, "fps": round(fps, 2)}
    out_json = out_root / "rtdetr_results.json"
    out_json.write_text(json.dumps(results, indent=2))

    print(f"\nVal   mAP@0.5:     {val_metrics['mAP50']:.4f}")
    print(f"Val   mAP@0.5:0.95: {val_metrics['mAP50_95']:.4f}")
    print(f"Test  mAP@0.5:     {test_metrics['mAP50']:.4f}")
    print(f"Test  mAP@0.5:0.95: {test_metrics['mAP50_95']:.4f}")
    print(f"FPS:               {fps:.1f}")
    print(f"\nResults → {out_json}")


if __name__ == "__main__":
    main()
