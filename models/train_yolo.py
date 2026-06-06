"""YOLOv8 training script.

Run locally:
    uv run python train_yolo.py

Run on Kaggle (from repo root):
    uv run python models/train_yolo.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import torch
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset import coco_to_yolo_labels, write_dataset_yaml
from metrics import measure_fps
from utils import get_paths, get_train_ann_path, set_seed

NC = 3
NAMES = ["motorbike", "helmet", "non-helmet"]
CKPT_NAME = "yolo_best.pt"
DEFAULT_RUN_NAME = "yolo_train"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 on helmet violation data.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model", type=str, default="yolov8m.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--lr0", type=float, default=1e-3)
    parser.add_argument("--lrf", type=float, default=0.01)
    parser.add_argument("--momentum", type=float, default=0.937)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    return parser.parse_args(argv)


def extract_metrics(r) -> dict:
    return {
        "mAP50": float(r.box.map50),
        "mAP50_95": float(r.box.map),
        "AR100": float(r.box.mr),
    }


def prepare_labels(data_root: Path, train_ann: Path, ann_dir: Path) -> Path:
    print("\nConverting COCO annotations to YOLO label format …")
    for split, ann_file in [
        ("train", train_ann),
        ("val", ann_dir / "instances_val.json"),
        ("test", ann_dir / "instances_test.json"),
    ]:
        coco_to_yolo_labels(ann_file, data_root, split)
    return ann_dir


def run(
    args: argparse.Namespace,
    *,
    eval_splits: tuple[str, ...] = ("val", "test"),
    save_checkpoint: bool = True,
    train: bool = True,
    load_checkpoint: bool = False,
    run_name: str = DEFAULT_RUN_NAME,
) -> dict:
    set_seed(args.seed)
    data_root, out_root = get_paths()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    print(f"Data:   {data_root}")
    print(f"Output: {out_root}")

    ann_dir = data_root / "annotations"
    train_ann = get_train_ann_path(data_root)
    print(f"Train annotations: {train_ann.name}")

    prepare_labels(data_root, train_ann, ann_dir)
    yaml_path = out_root / "dataset.yaml"
    write_dataset_yaml(yaml_path, data_root, NC, NAMES)
    print(f"Dataset YAML → {yaml_path}")

    dest_pt = out_root / CKPT_NAME
    model: YOLO | None = None

    if train:
        print(f"\nTraining {args.model} for {args.epochs} epochs …")
        model = YOLO(args.model)
        model.train(
            data=str(yaml_path),
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            lr0=args.lr0,
            lrf=args.lrf,
            momentum=args.momentum,
            weight_decay=args.weight_decay,
            device=device,
            seed=args.seed,
            project=str(out_root),
            name=run_name,
            exist_ok=True,
            verbose=True,
        )
        if save_checkpoint:
            best_pt = out_root / run_name / "weights" / "best.pt"
            if best_pt.exists():
                shutil.copy(best_pt, dest_pt)
                print(f"\nBest weights → {dest_pt}")
    else:
        ckpt = dest_pt if load_checkpoint and dest_pt.exists() else args.model
        if load_checkpoint:
            print(f"\nLoading checkpoint from {ckpt}")
        model = YOLO(str(ckpt))

    assert model is not None

    val_metrics: dict | None = None
    test_metrics: dict | None = None

    if "val" in eval_splits:
        print("\nEvaluating on val split …")
        val_results = model.val(data=str(yaml_path), split="val", device=device, verbose=False)
        val_metrics = extract_metrics(val_results)

    if "test" in eval_splits:
        print("\nEvaluating on test split …")
        test_results = model.val(data=str(yaml_path), split="test", device=device, verbose=False)
        test_metrics = extract_metrics(test_results)

    fps = 0.0
    if eval_splits:
        eval_model = YOLO(str(dest_pt)) if dest_pt.exists() else model
        dummy_input = torch.zeros(1, 3, args.imgsz, args.imgsz)
        fps = measure_fps(
            lambda x: eval_model.predict(x, verbose=False),
            dummy_input,
        )

    return {
        "val_mAP50": val_metrics["mAP50"] if val_metrics else None,
        "val_mAP50_95": val_metrics["mAP50_95"] if val_metrics else None,
        "val_loss": None,
        "test_mAP50": test_metrics["mAP50"] if test_metrics else None,
        "test_mAP50_95": test_metrics["mAP50_95"] if test_metrics else None,
        "fps": round(fps, 2),
        "val": val_metrics,
        "test": test_metrics,
    }


def main() -> None:
    args = parse_args()
    metrics = run(args)

    out_root = get_paths()[1]
    if metrics["val"] and metrics["test"]:
        results = {
            "val": metrics["val"],
            "test": metrics["test"],
            "fps": metrics["fps"],
        }
        out_json = out_root / "yolo_results.json"
        out_json.write_text(json.dumps(results, indent=2))

        print(f"\nVal   mAP@0.5:      {metrics['val_mAP50']:.4f}")
        print(f"Val   mAP@0.5:0.95: {metrics['val_mAP50_95']:.4f}")
        print(f"Test  mAP@0.5:      {metrics['test_mAP50']:.4f}")
        print(f"Test  mAP@0.5:0.95: {metrics['test_mAP50_95']:.4f}")
        print(f"FPS:                {metrics['fps']:.1f}")
        print(f"\nResults → {out_json}")


if __name__ == "__main__":
    main()
