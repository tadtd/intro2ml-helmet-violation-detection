"""Per-class evaluation of the three detectors on the test split.

Reports AP@0.5, AP@0.5:0.95 and AR@100 for every class separately instead of a
single averaged number. A combined mAP hides the class that matters most here:
`non-helmet` is only ~7% of the test annotations, so the two easy, frequent
classes dominate the average.

All three models are scored through the *same* COCOeval so the numbers are
directly comparable, regardless of each framework's own evaluator.

Run:
    uv run python eval_per_class.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from metrics import detection_confusion_matrix, precision_recall_f1_from_confusion
from utils import get_paths

NAMES = ["motorbike", "helmet", "non-helmet"]
CAT_IDS = [1, 2, 3]  # COCO category ids, aligned with NAMES
CKPT_DIR = Path(__file__).resolve().parent / "checkpoints"
CONF_FLOOR = 0.001  # keep low-score boxes so the PR curve (and AP) is complete


def resolve_data_root() -> Path:
    """Dataset root holding annotations/ and images/.

    `utils.get_paths()` assumes the data sits next to the model scripts; locally it
    lives at the repository root instead, so try both.
    """
    here = Path(__file__).resolve()
    candidates = [
        get_paths()[0],
        here.parent.parent.parent / "data",  # repo root /data
        here.parent.parent / "data",
    ]
    for candidate in candidates:
        if (candidate / "annotations" / "instances_test.json").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not find instances_test.json in: "
        + ", ".join(str(c) for c in candidates)
    )


def _image_records(coco: COCO) -> list[tuple[int, str]]:
    return [(img["id"], img["file_name"]) for img in coco.loadImgs(coco.getImgIds())]


def predict_ultralytics(weights: Path, img_dir: Path, coco: COCO, kind: str) -> list[dict]:
    """COCO-format predictions from a YOLO or RT-DETR checkpoint."""
    from ultralytics import RTDETR, YOLO

    model = YOLO(str(weights)) if kind == "yolo" else RTDETR(str(weights))
    preds: list[dict] = []
    for img_id, file_name in tqdm(_image_records(coco), desc=f"  {kind}"):
        result = model.predict(
            str(img_dir / file_name), conf=CONF_FLOOR, verbose=False,
        )[0]
        for box, score, cls in zip(
            result.boxes.xyxy.cpu().tolist(),
            result.boxes.conf.cpu().tolist(),
            result.boxes.cls.cpu().tolist(),
        ):
            x1, y1, x2, y2 = box
            preds.append({
                "image_id": img_id,
                "category_id": CAT_IDS[int(cls)],
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "score": float(score),
            })
    return preds


def predict_fasterrcnn(weights: Path, img_dir: Path, coco: COCO) -> list[dict]:
    """COCO-format predictions from the Torchvision Faster R-CNN checkpoint."""
    from PIL import Image
    from torchvision.transforms.functional import to_tensor

    from train_fasterrcnn import build_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(len(NAMES)).to(device)
    model.load_state_dict(torch.load(weights, map_location=device, weights_only=True))
    model.eval()

    preds: list[dict] = []
    with torch.no_grad():
        for img_id, file_name in tqdm(_image_records(coco), desc="  fasterrcnn"):
            image = to_tensor(Image.open(img_dir / file_name).convert("RGB")).to(device)
            output = model([image])[0]
            for box, score, label in zip(
                output["boxes"].cpu().tolist(),
                output["scores"].cpu().tolist(),
                output["labels"].cpu().tolist(),
            ):
                x1, y1, x2, y2 = box
                preds.append({
                    "image_id": img_id,
                    "category_id": int(label),
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "score": float(score),
                })
    return preds


def coco_eval(coco_gt: COCO, preds: list[dict], cat_ids: list[int] | None) -> dict:
    """AP/AR for one class (cat_ids=[id]) or for everything (cat_ids=None)."""
    coco_dt = coco_gt.loadRes(preds)
    evaluator = COCOeval(coco_gt, coco_dt, "bbox")
    if cat_ids is not None:
        evaluator.params.catIds = cat_ids
    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()
    return {
        "AP50_95": round(float(evaluator.stats[0]), 4),
        "AP50": round(float(evaluator.stats[1]), 4),
        "AR100": round(float(evaluator.stats[8]), 4),
    }


def evaluate(model_key: str, preds: list[dict], ann_path: Path, coco_gt: COCO) -> dict:
    per_class = {
        name: coco_eval(coco_gt, preds, [cat_id])
        for name, cat_id in zip(NAMES, CAT_IDS)
    }
    overall = coco_eval(coco_gt, preds, None)

    # Precision/recall/F1 per class at the operating point used for reporting.
    matrix = detection_confusion_matrix(
        ann_path, preds, num_classes=len(NAMES), iou_threshold=0.5, score_threshold=0.25,
    )
    cls_metrics = precision_recall_f1_from_confusion(matrix, len(NAMES))
    for index, name in enumerate(NAMES):
        per_class[name]["precision"] = round(float(cls_metrics["precision_by_class"][index]), 4)
        per_class[name]["recall"] = round(float(cls_metrics["recall_by_class"][index]), 4)
        per_class[name]["f1"] = round(float(cls_metrics["f1_by_class"][index]), 4)

    return {"per_class": per_class, "overall": overall, "confusion_matrix": matrix.tolist()}


def main() -> None:
    data_root = resolve_data_root()
    out_root = get_paths()[1]
    ann_path = data_root / "annotations" / "instances_test.json"
    img_dir = data_root / "images" / "test"
    coco_gt = COCO(str(ann_path))

    counts = {name: 0 for name in NAMES}
    for ann in coco_gt.loadAnns(coco_gt.getAnnIds()):
        counts[NAMES[CAT_IDS.index(ann["category_id"])]] += 1
    print(f"\nTest annotations per class: {counts}\n")

    jobs = [
        ("yolo", lambda: predict_ultralytics(CKPT_DIR / "yolo_best.pt", img_dir, coco_gt, "yolo")),
        ("rtdetr", lambda: predict_ultralytics(CKPT_DIR / "rtdetr_best.pt", img_dir, coco_gt, "rtdetr")),
        ("fasterrcnn", lambda: predict_fasterrcnn(CKPT_DIR / "fasterrcnn_best.pth", img_dir, coco_gt)),
    ]

    results: dict = {"test_annotations_per_class": counts, "models": {}}
    for key, predict in jobs:
        print(f"\n=== {key} ===")
        preds = predict()
        if not preds:
            print(f"  no predictions for {key}; skipping")
            continue
        results["models"][key] = evaluate(key, preds, ann_path, coco_gt)

    out_json = out_root / "per_class_results.json"
    out_json.write_text(json.dumps(results, indent=2))

    print("\n\n================ PER-CLASS TEST RESULTS ================")
    header = f"{'model':<12}{'class':<13}{'AP50':>8}{'AP50-95':>9}{'P':>8}{'R':>8}{'F1':>8}"
    print(header)
    print("-" * len(header))
    for key, data in results["models"].items():
        for name in NAMES:
            m = data["per_class"][name]
            print(
                f"{key:<12}{name:<13}{m['AP50']:>8.3f}{m['AP50_95']:>9.3f}"
                f"{m['precision']:>8.3f}{m['recall']:>8.3f}{m['f1']:>8.3f}"
            )
        o = data["overall"]
        print(f"{key:<12}{'ALL (mAP)':<13}{o['AP50']:>8.3f}{o['AP50_95']:>9.3f}")
        print("-" * len(header))
    print(f"\nSaved → {out_json}")


if __name__ == "__main__":
    main()
