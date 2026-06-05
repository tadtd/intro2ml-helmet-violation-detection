"""Faster R-CNN (ResNet50-FPN) training script.

Run locally:
    uv run python train_fasterrcnn.py

Run on Kaggle (from repo root):
    uv run python train/train_fasterrcnn.py
"""

import json
import sys
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
from metrics import evaluate_coco, measure_fps
from utils import get_paths, set_seed

# ── Config ────────────────────────────────────────────────────────────────────
SEED         = 42
EPOCHS       = 50
BATCH_SIZE   = 4
LR           = 1e-3
MOMENTUM     = 0.9
WEIGHT_DECAY = 5e-4
LR_STEP      = 10
LR_GAMMA     = 0.1
NC           = 3
NAMES        = ["motorbike", "helmet", "non-helmet"]
NUM_WORKERS  = 2
# ─────────────────────────────────────────────────────────────────────────────


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
                        "bbox": [x1, y1, x2 - x1, y2 - y1],  # xyxy → xywh
                        "score": score,
                    })
    return predictions


def main() -> None:
    set_seed(SEED)
    data_root, out_root = get_paths()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Data:   {data_root}")
    print(f"Output: {out_root}")

    ann_dir  = data_root / "annotations"
    img_dir  = data_root / "images"

    merged = ann_dir / "instances_train_merged.json"
    train_ann = merged if merged.exists() else ann_dir / "instances_train.json"
    print(f"Train annotations: {train_ann.name}")

    train_ds = CocoDetectionDataset(train_ann, img_dir / "train")
    val_ds   = CocoDetectionDataset(ann_dir / "instances_val.json",   img_dir / "val")
    test_ds  = CocoDetectionDataset(ann_dir / "instances_test.json",  img_dir / "test")

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, collate_fn=CocoDetectionDataset.collate_fn,
    )
    val_loader = DataLoader(
        val_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, collate_fn=CocoDetectionDataset.collate_fn,
    )
    test_loader = DataLoader(
        test_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, collate_fn=CocoDetectionDataset.collate_fn,
    )

    model = build_model(NC).to(device)
    optimizer = SGD(
        model.parameters(), lr=LR, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY
    )
    scheduler = StepLR(optimizer, step_size=LR_STEP, gamma=LR_GAMMA)

    ckpt_path = out_root / "fasterrcnn_best.pth"
    best_val_loss = float("inf")

    print(f"\nTraining for {EPOCHS} epochs …")
    for epoch in range(1, EPOCHS + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss   = compute_val_loss(model, val_loader, device)
        scheduler.step()
        print(f"Epoch {epoch:3d}/{EPOCHS}  train={train_loss:.4f}  val={val_loss:.4f}")
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), ckpt_path)
            print(f"  → saved best checkpoint ({ckpt_path.name})")

    print(f"\nLoading best checkpoint from {ckpt_path}")
    model.load_state_dict(torch.load(ckpt_path, map_location=device))

    print("\nEvaluating …")
    val_preds  = predict(model, val_loader,  device)
    test_preds = predict(model, test_loader, device)

    val_metrics  = evaluate_coco(ann_dir / "instances_val.json",  val_preds)
    test_metrics = evaluate_coco(ann_dir / "instances_test.json", test_preds)

    dummy_input = [torch.zeros(3, 640, 640, device=device)]
    fps = measure_fps(lambda x: model(x), dummy_input)

    results = {"val": val_metrics, "test": test_metrics, "fps": round(fps, 2)}
    out_json = out_root / "fasterrcnn_results.json"
    out_json.write_text(json.dumps(results, indent=2))

    print(f"\nVal   mAP@0.5:     {val_metrics['mAP50']:.4f}")
    print(f"Val   mAP@0.5:0.95: {val_metrics['mAP50_95']:.4f}")
    print(f"Test  mAP@0.5:     {test_metrics['mAP50']:.4f}")
    print(f"Test  mAP@0.5:0.95: {test_metrics['mAP50_95']:.4f}")
    print(f"FPS:               {fps:.1f}")
    print(f"\nResults → {out_json}")


if __name__ == "__main__":
    main()
