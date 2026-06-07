# Helmet Violation Detection — Training Plan

Object detection pipeline for helmet violation on motorbikes. Three detectors are trained and compared: **YOLOv8m**, **Faster R-CNN (ResNet50-FPN)**, and **RT-DETR-L**. All code lives under `models/`, runs with **`uv`**, and is designed to execute on **Kaggle** via Jupyter notebooks that call Python scripts with **argparse** CLI flags.

---

## 1. Dataset

The dataset lives in `data/` (see [`data/README.md`](../data/README.md)). Annotations are **COCO JSON**; images are pre-letterboxed to **640×640**.

### Classes

| id | name         | supercategory |
|----|--------------|---------------|
| 1  | `motorbike`  | vehicle       |
| 2  | `helmet`     | safety        |
| 3  | `non-helmet` | violation     |

### Splits and roles

| Split | Images | Annotations | Annotation file | Role |
|-------|-------:|------------:|-----------------|------|
| **Train** | 2,309 | 11,047 | `instances_train_merged.json` | Model training |
| **Validation** | 330 | 1,889 | `instances_val.json` | Ray Tune hyperparameter selection |
| **Test** | 659 | 1,861 | `instances_test.json` | Final evaluation (once, after training) |

The train set was built from multiple sources with **partial annotations**. The merged train file combines manual labels with pseudo-labels so all three classes are covered. **Val and test are never modified.**

```
data/
├── annotations/
│   ├── instances_train.json          ← original manual labels (reference)
│   ├── instances_train_merged.json   ← used for training
│   ├── instances_val.json
│   └── instances_test.json
└── images/
    ├── train/
    ├── val/
    └── test/
```

Training scripts pick `instances_train_merged.json` automatically via `get_train_ann_path()`; if missing, they fall back to `instances_train.json`.

---

## 2. Models

| Model                  | Type              | Approx. FPS | COCO mAP@0.5:0.95 |
|------------------------|-------------------|------------:|------------------:|
| YOLOv8m                | Single-stage CNN  |        ~120 |             ~50.2 |
| Faster R-CNN (R50-FPN) | Two-stage CNN     |         ~15 |             ~46.7 |
| RT-DETR-L              | Transformer       |        ~100 |             ~53.4 |

|                        | YOLOv8m            | Faster R-CNN            | RT-DETR-L               |
|------------------------|--------------------|-------------------------|-------------------------|
| Training API           | Ultralytics        | torchvision             | Ultralytics             |
| Default weights        | `yolov8m.pt`       | ResNet50-FPN COCO       | `rtdetr-l.pt`           |
| Train script           | `train_yolo.py`    | `train_fasterrcnn.py`   | `train_rtdetr.py`       |
| Tune orchestrator      | `raytune.py --model yolo` | `raytune.py --model fasterrcnn` | `raytune.py --model rtdetr` |
| Kaggle notebook        | `yolo.ipynb`       | `faster-rcnn.ipynb`     | `rtdetr.ipynb`          |

---

## 3. Training workflow

### Recommended pipeline (Kaggle): Ray Tune → final train → test eval

All three models follow the same **two-phase** workflow via `raytune.py`:

```
Phase 1 — Ray Tune (validation only)
  • Run NUM_SAMPLES trials on the train split
  • Each trial evaluates on val → metric val_mAP50_95
  • Test is NEVER used
  • Output: raytune/{model}/best_config.json

Phase 2 — Final train + test evaluation
  • Train from scratch with best hyperparameters (EPOCHS epochs)
  • Weights initialized from pretrained checkpoint (not from trial checkpoints)
  • Checkpoint selected using val (Faster R-CNN: val loss; YOLO/RT-DETR: Ultralytics best.pt)
  • Immediately evaluate on test at the end of training
  • Output: {model}_best.* + {model}_final_results.json
```

**Rules:**
- Test is not used during Ray Tune or hyperparameter selection.
- Final reported metrics come from the **test** split after Phase 2 training completes.
- Use `--tune-epochs` < `--epochs` to speed up Phase 1 (e.g. tune 20 epochs, final train 50).

### Direct training (no Ray Tune)

Run `train_*.py` directly to train once with fixed hyperparameters via CLI. Evaluates on **both val and test**, writes `*_results.json`. Useful when you already have `best_config.json` and want to reproduce a run manually.

---

## 4. Project structure

```
models/
├── PLAN.md
├── pyproject.toml              ← uv dependencies (includes ray[tune])
│
├── utils.py                    ← set_seed, get_paths, get_train_ann_path
├── dataset.py                  ← CocoDetectionDataset, coco_to_yolo_labels, write_dataset_yaml
├── metrics.py                  ← evaluate_coco, measure_fps
│
├── train_fasterrcnn.py         ← Faster R-CNN: parse_args() + run()
├── train_yolo.py               ← YOLOv8: parse_args() + run()
├── train_rtdetr.py             ← RT-DETR: parse_args() + run()
├── raytune.py                  ← Ray Tune orchestrator (Phase 1 + Phase 2)
│
├── faster-rcnn.ipynb           ← Kaggle notebook
├── yolo.ipynb
└── rtdetr.ipynb
```

Each `train_*.py` exposes:

```python
def parse_args(argv=None) -> argparse.Namespace: ...
def run(args, *, eval_splits=("val", "test"), save_checkpoint=True, train=True, ...) -> dict: ...
def main() -> None: ...
```

`raytune.py` imports `run()` from the train scripts and controls `eval_splits` per phase.

---

## 5. Setup

### 5.1 Dependencies (`pyproject.toml`)

```toml
[project]
name = "helmet-violation-detection"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "torch",
  "torchvision",
  "ultralytics",
  "pycocotools",
  "torchmetrics[detection]",
  "numpy",
  "Pillow",
  "tqdm",
  "pyyaml",
  "ray[tune]",
]
```

### 5.2 Local

```bash
cd models/
uv sync

# Direct train (defaults)
uv run python train_fasterrcnn.py
uv run python train_yolo.py
uv run python train_rtdetr.py

# With custom hyperparameters
uv run python train_fasterrcnn.py --epochs 30 --batch-size 8 --lr 0.0003

# Full Ray Tune pipeline
uv run python raytune.py --model fasterrcnn --num-samples 10 --tune-epochs 20 --epochs 50
```

Data is read from `../data/` automatically.

### 5.3 Path resolution (Kaggle)

Set `DATA_PATH` and `MPLBACKEND` in the notebook before running scripts:

```python
import os

DATA_PATH = "/kaggle/input/your-dataset-slug"  # edit this
os.environ["DATA_PATH"] = DATA_PATH
os.environ["MPLBACKEND"] = "Agg"
```

| Variable      | Local       | Kaggle |
|---------------|-------------|--------|
| Input dataset | `../data`   | `DATA_PATH` |
| `data_root`   | `../data`   | `/kaggle/working/data` (annotations copied; images symlinked) |
| `out_root`    | `models/output/` | `/kaggle/working` |

---

## 6. CLI reference (argparse)

### `raytune.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | *(required)* | `fasterrcnn`, `yolo`, or `rtdetr` |
| `--num-samples` | 10 | Number of Ray Tune trials |
| `--max-concurrent` | 1 | Concurrent trials |
| `--epochs` | 50 | Epochs for Phase 2 final training |
| `--tune-epochs` | = `--epochs` | Epochs per tune trial |
| `--seed` | 42 | Random seed |
| `--storage-path` | `output/raytune/{model}` | Ray artifacts directory |
| `--skip-retrain` | off | Phase 1 only (skip final train + test) |

Example:

```bash
uv run python models/raytune.py \
  --model fasterrcnn \
  --num-samples 10 \
  --max-concurrent 1 \
  --epochs 50 \
  --tune-epochs 20 \
  --seed 42
```

### `train_fasterrcnn.py`

| Flag | Default |
|------|---------|
| `--seed` | 42 |
| `--epochs` | 50 |
| `--batch-size` | 4 |
| `--lr` | 1e-3 |
| `--momentum` | 0.9 |
| `--weight-decay` | 5e-4 |
| `--lr-step` | 10 |
| `--lr-gamma` | 0.1 |
| `--num-workers` | 2 |

Model: `fasterrcnn_resnet50_fpn(weights="DEFAULT")` with `FastRCNNPredictor` head for 4 classes (background + 3). Optimiser: SGD + StepLR. Best checkpoint saved by **val loss**.

### `train_yolo.py`

| Flag | Default |
|------|---------|
| `--seed` | 42 |
| `--model` | `yolov8m.pt` |
| `--epochs` | 50 |
| `--batch` | 16 |
| `--imgsz` | 640 |
| `--lr0` | 1e-3 |
| `--lrf` | 0.01 |
| `--momentum` | 0.937 |
| `--weight-decay` | 5e-4 |

Converts COCO → YOLO labels, trains via `YOLO(...).train(...)`, evaluates with `model.val()`.

### `train_rtdetr.py`

Same flags as YOLO; defaults differ:

| Flag | Default |
|------|---------|
| `--model` | `rtdetr-l.pt` |
| `--batch` | 8 |
| `--lr0` | 1e-4 |
| `--optimizer` | `AdamW` |
| `--force-labels` | off |

Uses `RTDETR(...)` instead of `YOLO(...)`. RT-DETR fixes `optimizer=AdamW` by default so `lr0`, `momentum`, and `weight_decay` are actually honored instead of being ignored by Ultralytics `optimizer=auto`.

---

## 7. Ray Tune search spaces

Phase 1 optimizes **`val_mAP50_95`** (max) with ASHA scheduler.

**Faster R-CNN:** `lr`, `batch_size`, `weight_decay`, `lr_step`, `lr_gamma`

| Parameter | Search |
|-----------|--------|
| `lr` | log-uniform [1e-4, 1e-2] |
| `batch_size` | choice {2, 4, 8} |
| `weight_decay` | log-uniform [1e-5, 1e-3] |
| `lr_step` | choice {5, 10, 15} |
| `lr_gamma` | choice {0.1, 0.5} |

**YOLO:** `lr0`, `batch`, `lrf`, `weight_decay`

| Parameter | Search |
|-----------|--------|
| `lr0` | log-uniform [1e-4, 1e-2] |
| `batch` | choice {8, 16, 32} |
| `lrf` | uniform [0.01, 0.2] |
| `weight_decay` | log-uniform [1e-5, 1e-3] |

**RT-DETR:** same as YOLO except `lr0` ∈ [1e-5, 1e-3], `batch` ∈ {2, 4, 8}, and fixed `optimizer=AdamW`.

Example `best_config.json`:

```json
{
  "lr": 0.0003,
  "batch_size": 4,
  "weight_decay": 0.0001,
  "lr_step": 10,
  "lr_gamma": 0.1,
  "val_mAP50_95": 0.4521
}
```

To retrain manually without Ray Tune:

```bash
uv run python train_fasterrcnn.py \
  --lr 0.0003 --batch-size 4 --weight-decay 0.0001 --lr-step 10 --lr-gamma 0.1
```

---

## 8. Kaggle notebooks

All notebooks share the same setup: clone repo → install `uv` → pin Python 3.13 → write `pyproject.toml` → `uv sync` → set `DATA_PATH`.

### Run cell

Pass hyperparameters via **argparse CLI** (always include `python` in the command):

```bash
!uv run python models/raytune.py --model fasterrcnn --num-samples 10 --epochs 50 --tune-epochs 20 --seed 42
```

Notebooks `yolo.ipynb` and `rtdetr.ipynb` also include a **Config cell** that builds `RUN_CMD` from Python variables and runs `!{RUN_CMD}` — useful for editing parameters without touching the shell command directly.

Direct train (no Ray Tune):

```bash
!uv run python models/train_yolo.py --epochs 50 --batch 16 --lr0 0.001
```

---

## 9. Shared modules

### `utils.py`

| Function | Description |
|----------|-------------|
| `set_seed(seed=42)` | Seeds `random`, `numpy`, `torch`, CUDA |
| `get_paths()` | Returns `(data_root, out_root)` with Kaggle auto-detection |
| `get_train_ann_path(data_root)` | Returns merged train JSON if present, else original |

### `dataset.py`

| Symbol | Description |
|--------|-------------|
| `CocoDetectionDataset` | PyTorch `Dataset` for Faster R-CNN (xyxy boxes, collate_fn) |
| `coco_to_yolo_labels(...)` | Writes YOLO `.txt` labels to `data_root/labels/{split}/` |
| `write_dataset_yaml(...)` | Writes Ultralytics `dataset.yaml` |

### `metrics.py`

| Function | Description |
|----------|-------------|
| `evaluate_coco(gt_ann_json, predictions)` | COCOeval → `{mAP50, mAP50_95, AR100}` |
| `measure_fps(model_fn, dummy_input)` | Inference throughput (FPS) |

---

## 10. Outputs

```
out_root/   (models/output/ locally, /kaggle/working/ on Kaggle)

# Ray Tune pipeline
├── raytune/
│   ├── fasterrcnn/
│   │   ├── best_config.json
│   │   └── ray_trials/
│   ├── yolo/
│   └── rtdetr/
├── fasterrcnn_best.pth
├── fasterrcnn_final_results.json
├── yolo_best.pt
├── yolo_final_results.json
├── rtdetr_best.pt
└── rtdetr_final_results.json

# Direct train (train_*.py)
├── fasterrcnn_results.json
├── yolo_results.json
└── rtdetr_results.json
```

**`*_final_results.json`** (Ray Tune pipeline):

```json
{
  "best_config": { "lr": 0.0003, "batch_size": 4, "..." : "..." },
  "test": { "mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0 },
  "fps": 0.0,
  "tune_val_mAP50_95": 0.4521
}
```

**`*_results.json`** (direct train):

```json
{
  "val":  { "mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0 },
  "test": { "mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0 },
  "fps":  0.0
}
```

Use the Phase 2 checkpoint (`*_best.*`) with test metrics from `*_final_results.json` for deployment.

---

## 11. Key design decisions

- **Train / val / test separation.** Tune selects hyperparameters on val only; test is evaluated once after final training.
- **Pre-merged train annotations.** Partial-label problem handled offline; scripts train on `instances_train_merged.json`.
- **Val and test never modified.** Evaluation sets stay human-annotated.
- **Images pre-letterboxed at 640×640.** `IMGSZ=640` for YOLO/RT-DETR; Faster R-CNN uses 640×640 inputs as-is.
- **argparse everywhere.** All hyperparameters controlled via CLI; notebooks pass flags explicitly.
- **Ray Tune on Kaggle.** `ray[tune]` required; training runs on Linux (Kaggle GPU kernels).
- **`uv` for dependencies.** `pyproject.toml` + `uv sync` + `uv run python <script>`.
- **Thin notebooks, fat scripts.** Shared logic in `utils.py`, `dataset.py`, `metrics.py`; one train script per model plus `raytune.py` orchestrator.
