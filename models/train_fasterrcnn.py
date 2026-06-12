"""Faster R-CNN (ResNet50-FPN) training script.

Run locally:
    uv run python train_fasterrcnn.py

Run on Kaggle (from repo root):
    uv run python models/train_fasterrcnn.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

import torch
from torch.optim import SGD
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DataLoader
from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_Weights,
    fasterrcnn_resnet50_fpn,
)
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset import CocoDetectionDataset
from metrics import (
    detection_confusion_matrix,
    evaluate_coco,
    measure_fps,
    precision_recall_f1_from_confusion,
)
from plots import (
    learning_curve_comment,
    plot_confusion_matrix,
    plot_learning_curves,
    write_confusion_matrix_csv,
    write_learning_curves_csv,
)
from utils import get_paths, get_train_ann_path, set_seed

NC = 3
NAMES = ["motorbike", "helmet", "non-helmet"]
CKPT_NAME = "fasterrcnn_best.pth"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Faster R-CNN on helmet violation data.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--momentum", type=float, default=0.9)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--lr-step", type=int, default=10)
    parser.add_argument("--lr-gamma", type=float, default=0.1)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--conf-thres", type=float, default=0.25)
    parser.add_argument("--iou-thres", type=float, default=0.5)
    return parser.parse_args(argv)


def build_model(nc: int) -> torch.nn.Module:
    model = fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, nc + 1)
    return model


def train_one_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    for images, targets in tqdm(loader, desc="  train", leave=False):
        images = [img.to(device) for img in images]
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
        loss_dict = model(images, targets)
        loss = sum(loss_dict.values())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def compute_val_loss(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    with torch.no_grad():
        for images, targets in tqdm(loader, desc="  val  ", leave=False):
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            loss_dict = model(images, targets)
            total_loss += sum(loss_dict.values()).item()
    return total_loss / len(loader)


def predict(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> list[dict]:
    model.eval()
    predictions = []
    with torch.no_grad():
        for images, targets in tqdm(loader, desc="  infer", leave=False):
            images = [img.to(device) for img in images]
            outputs = model(images)
            for target, output in zip(targets, outputs):
                img_id = int(target["image_id"].item())
                for box, score, label in zip(
                    output["boxes"].cpu().tolist(),
                    output["scores"].cpu().tolist(),
                    output["labels"].cpu().tolist(),
                ):
                    x1, y1, x2, y2 = box
                    predictions.append({
                        "image_id": img_id,
                        "category_id": label,
                        "bbox": [x1, y1, x2 - x1, y2 - y1],
                        "score": score,
                    })
    return predictions


def run(
    args: argparse.Namespace,
    *,
    on_epoch_end: Callable[..., None] | None = None,
    eval_splits: tuple[str, ...] = ("val", "test"),
    save_checkpoint: bool = True,
    train: bool = True,
    load_checkpoint: bool = False,
) -> dict:
    set_seed(args.seed)
    data_root, out_root = get_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Data:   {data_root}")
    print(f"Output: {out_root}")

    ann_dir = data_root / "annotations"
    img_dir = data_root / "images"
    train_ann = get_train_ann_path(data_root)
    print(f"Train annotations: {train_ann.name}")

    train_ds = CocoDetectionDataset(train_ann, img_dir / "train")
    val_ds = CocoDetectionDataset(ann_dir / "instances_val.json", img_dir / "val")
    test_ds = CocoDetectionDataset(ann_dir / "instances_test.json", img_dir / "test")

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=CocoDetectionDataset.collate_fn,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=CocoDetectionDataset.collate_fn,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=CocoDetectionDataset.collate_fn,
    )

    ckpt_path = out_root / CKPT_NAME
    model = build_model(NC).to(device)
    last_val_loss: float | None = None
    history: list[dict] = []

    if train:
        optimizer = SGD(
            model.parameters(),
            lr=args.lr,
            momentum=args.momentum,
            weight_decay=args.weight_decay,
        )
        scheduler = StepLR(optimizer, step_size=args.lr_step, gamma=args.lr_gamma)
        best_val_loss = float("inf")

        print(f"\nTraining for {args.epochs} epochs …")
        for epoch in range(1, args.epochs + 1):
            train_loss = train_one_epoch(model, train_loader, optimizer, device)
            val_loss = compute_val_loss(model, val_loader, device)
            last_val_loss = val_loss
            scheduler.step()
            history.append({
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "lr": scheduler.get_last_lr()[0],
            })
            print(f"Epoch {epoch:3d}/{args.epochs}  train={train_loss:.4f}  val={val_loss:.4f}")
            if on_epoch_end is not None:
                on_epoch_end(epoch, train_loss=train_loss, val_loss=val_loss)
            if save_checkpoint and val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), ckpt_path)
                print(f"  → saved best checkpoint ({ckpt_path.name})")
        if save_checkpoint and ckpt_path.exists() and eval_splits:
            print(f"\nLoading best checkpoint from {ckpt_path}")
            model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))
    elif load_checkpoint and ckpt_path.exists():
        print(f"\nLoading checkpoint from {ckpt_path}")
        model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))

    val_metrics: dict | None = None
    test_metrics: dict | None = None
    val_preds: list[dict] | None = None
    test_preds: list[dict] | None = None

    if "val" in eval_splits:
        print("\nEvaluating on val …")
        val_preds = predict(model, val_loader, device)
        val_metrics = evaluate_coco(ann_dir / "instances_val.json", val_preds)

    if "test" in eval_splits:
        print("\nEvaluating on test …")
        test_preds = predict(model, test_loader, device)
        test_metrics = evaluate_coco(ann_dir / "instances_test.json", test_preds)

    fps = 0.0
    if eval_splits:
        dummy_input = [torch.zeros(3, 640, 640, device=device)]
        fps = measure_fps(lambda x: model(x), dummy_input)

    return {
        "val_mAP50": val_metrics["mAP50"] if val_metrics else None,
        "val_mAP50_95": val_metrics["mAP50_95"] if val_metrics else None,
        "val_loss": last_val_loss,
        "test_mAP50": test_metrics["mAP50"] if test_metrics else None,
        "test_mAP50_95": test_metrics["mAP50_95"] if test_metrics else None,
        "fps": round(fps, 2),
        "val": val_metrics,
        "test": test_metrics,
        "history": history,
        "val_predictions": val_preds,
        "test_predictions": test_preds,
    }


def main() -> None:
    args = parse_args()
    metrics = run(args)

    data_root, out_root = get_paths()
    if metrics["val"] and metrics["test"]:
        history = metrics.get("history") or []
        if history:
            history_json = out_root / "fasterrcnn_history.json"
            history_json.write_text(json.dumps(history, indent=2))
            write_learning_curves_csv(history, out_root / "fasterrcnn_learning_curves.csv")
            plot_learning_curves(history, out_root / "fasterrcnn_learning_curves.png")
            (out_root / "fasterrcnn_learning_curve_comment.txt").write_text(
                learning_curve_comment(history),
            )

        test_preds = metrics.get("test_predictions") or []
        cm = detection_confusion_matrix(
            data_root / "annotations" / "instances_test.json",
            test_preds,
            num_classes=NC,
            iou_threshold=args.iou_thres,
            score_threshold=args.conf_thres,
        )
        cls_metrics = precision_recall_f1_from_confusion(cm, NC)
        write_confusion_matrix_csv(cm, NAMES, out_root / "fasterrcnn_confusion_matrix.csv")
        plot_confusion_matrix(cm, NAMES, out_root / "fasterrcnn_confusion_matrix.png")

        results = {
            "val": metrics["val"],
            "test": metrics["test"],
            "test_classification_metrics": cls_metrics,
            "confusion_matrix": cm.tolist(),
            "confusion_matrix_iou_threshold": args.iou_thres,
            "confusion_matrix_score_threshold": args.conf_thres,
            "fps": metrics["fps"],
        }
        out_json = out_root / "fasterrcnn_results.json"
        out_json.write_text(json.dumps(results, indent=2))

        print(f"\nVal   mAP@0.5:      {metrics['val_mAP50']:.4f}")
        print(f"Val   mAP@0.5:0.95: {metrics['val_mAP50_95']:.4f}")
        print(f"Test  mAP@0.5:      {metrics['test_mAP50']:.4f}")
        print(f"Test  mAP@0.5:0.95: {metrics['test_mAP50_95']:.4f}")
        print(f"FPS:                {metrics['fps']:.1f}")
        print(f"\nResults → {out_json}")


if __name__ == "__main__":
    main()
