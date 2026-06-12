import time
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval


def evaluate_coco(gt_ann_json: Path, predictions: list[dict]) -> dict:
    """Run COCO bounding-box evaluation.

    Args:
        gt_ann_json: Path to a COCO-format ground-truth annotation JSON.
        predictions: List of dicts with keys:
            image_id    (int)
            category_id (int)
            bbox        ([x, y, w, h] in pixels, top-left origin)
            score       (float)

    Returns:
        {"mAP50": float, "mAP50_95": float, "AR100": float}
    """
    if not predictions:
        return {"mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0}

    coco_gt = COCO(str(gt_ann_json))
    coco_dt = coco_gt.loadRes(predictions)

    evaluator = COCOeval(coco_gt, coco_dt, iouType="bbox")
    evaluator.evaluate()
    evaluator.accumulate()
    evaluator.summarize()

    stats = evaluator.stats
    return {
        "mAP50_95": float(stats[0]),
        "mAP50": float(stats[1]),
        "AR100": float(stats[8]),
    }


def measure_fps(
    model_fn: Callable,
    dummy_input,
    warmup: int = 10,
    runs: int = 100,
) -> float:
    """Measure inference throughput.

    Args:
        model_fn:    Callable that takes dummy_input and returns any output.
        dummy_input: Input passed to model_fn on every call.
        warmup:      Number of warm-up calls (excluded from timing).
        runs:        Number of timed calls.

    Returns:
        Frames per second (float).
    """
    use_cuda = torch.cuda.is_available()

    with torch.no_grad():
        for _ in range(warmup):
            model_fn(dummy_input)

    if use_cuda:
        torch.cuda.synchronize()

    start = time.perf_counter()
    with torch.no_grad():
        for _ in range(runs):
            model_fn(dummy_input)

    if use_cuda:
        torch.cuda.synchronize()

    elapsed = time.perf_counter() - start
    return runs / elapsed


def _xywh_to_xyxy(box: list[float]) -> list[float]:
    x, y, w, h = box
    return [x, y, x + w, y + h]


def _box_iou_xyxy(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def detection_confusion_matrix(
    gt_ann_json: Path,
    predictions: list[dict],
    *,
    num_classes: int,
    iou_threshold: float = 0.5,
    score_threshold: float = 0.25,
) -> np.ndarray:
    """Build a detection confusion matrix with an extra background row/column.

    Rows are ground truth classes; columns are predicted classes. The last row is
    false positives on background and the last column is missed ground truths.
    Category IDs are expected to be 1-indexed.
    """
    coco = COCO(str(gt_ann_json))
    matrix = np.zeros((num_classes + 1, num_classes + 1), dtype=np.int64)

    preds_by_image: dict[int, list[dict]] = {}
    for pred in predictions:
        if pred.get("score", 1.0) < score_threshold:
            continue
        preds_by_image.setdefault(int(pred["image_id"]), []).append(pred)

    for image_id in coco.imgs:
        anns = coco.loadAnns(coco.getAnnIds(imgIds=image_id))
        gt_items = [
            {
                "label": int(ann["category_id"]) - 1,
                "box": _xywh_to_xyxy(ann["bbox"]),
            }
            for ann in anns
        ]
        pred_items = sorted(
            [
                {
                    "label": int(pred["category_id"]) - 1,
                    "box": _xywh_to_xyxy(pred["bbox"]),
                    "score": float(pred.get("score", 1.0)),
                }
                for pred in preds_by_image.get(image_id, [])
            ],
            key=lambda item: item["score"],
            reverse=True,
        )

        matched_gt: set[int] = set()
        for pred in pred_items:
            best_idx = None
            best_iou = 0.0
            for idx, gt in enumerate(gt_items):
                if idx in matched_gt:
                    continue
                iou = _box_iou_xyxy(pred["box"], gt["box"])
                if iou > best_iou:
                    best_iou = iou
                    best_idx = idx

            pred_label = pred["label"]
            if best_idx is not None and best_iou >= iou_threshold:
                gt_label = gt_items[best_idx]["label"]
                matrix[gt_label, pred_label] += 1
                matched_gt.add(best_idx)
            else:
                matrix[num_classes, pred_label] += 1

        for idx, gt in enumerate(gt_items):
            if idx not in matched_gt:
                matrix[gt["label"], num_classes] += 1

    return matrix


def precision_recall_f1_from_confusion(matrix: np.ndarray, num_classes: int) -> dict:
    tp = np.diag(matrix[:num_classes, :num_classes]).astype(float)
    fp = matrix[:, :num_classes].sum(axis=0).astype(float) - tp
    fn = matrix[:num_classes, :].sum(axis=1).astype(float) - tp

    precision_by_class = np.divide(tp, tp + fp, out=np.zeros_like(tp), where=(tp + fp) > 0)
    recall_by_class = np.divide(tp, tp + fn, out=np.zeros_like(tp), where=(tp + fn) > 0)
    f1_by_class = np.divide(
        2 * precision_by_class * recall_by_class,
        precision_by_class + recall_by_class,
        out=np.zeros_like(tp),
        where=(precision_by_class + recall_by_class) > 0,
    )

    correct = float(tp.sum())
    total = float(matrix.sum())
    return {
        "accuracy": correct / total if total else 0.0,
        "precision": float(precision_by_class.mean()),
        "recall": float(recall_by_class.mean()),
        "f1": float(f1_by_class.mean()),
        "precision_by_class": precision_by_class.tolist(),
        "recall_by_class": recall_by_class.tolist(),
        "f1_by_class": f1_by_class.tolist(),
    }
