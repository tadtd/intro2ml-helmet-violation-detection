import time
from pathlib import Path
from typing import Callable

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
