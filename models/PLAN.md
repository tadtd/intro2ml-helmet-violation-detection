# Helmet Violation Detection — Training Plan

Object detection pipeline for helmet violation on motorbikes. Three detectors are trained and compared: **YOLOv8m**, **Faster R-CNN (ResNet50-FPN)**, and **RT-DETR-L**. All code lives under `train/`, runs with **`uv`**, and is designed to execute on **Kaggle** via thin Jupyter notebooks that call Python scripts.

---

## 1. Dataset

### Classes

| id | name         | supercategory |
|----|--------------|---------------|
| 1  | `motorbike`  | vehicle       |
| 2  | `helmet`     | safety        |
| 3  | `non-helmet` | violation     |

### Splits

| Split | Images | Annotations | Avg ann/image |
|-------|-------:|------------:|--------------:|
| train |  2,309 |       6,965 |           3.0 |
| val   |    330 |       1,889 |           5.7 |
| test  |    659 |       1,861 |           2.8 |

### Format

- **COCO JSON** — `data/annotations/instances_{train,val,test}.json`
- Bounding boxes: pixel-space `[x, y, w, h]` (top-left origin, not normalised)
- Images are **pre-letterboxed to 640×640** (grey padding RGB 114) — use `IMGSZ=640` everywhere, no resize step needed
- Each image record includes provenance fields: `source_name`, `source_split`, `group_key`, etc.
- **`val` and `test` are never modified** by the data pipeline

```
data/
├── annotations/
│   ├── instances_train.json          ← original (untouched)
│   ├── instances_val.json
│   ├── instances_test.json
│   ├── instances_train_merged.json   ← produced by data pipeline (final train file)
│   └── pseudo_labels.json            ← auto-generated labels only
└── images/
    ├── train/    ← 2,309 × 640×640 JPEG
    ├── val/      ←   330 × 640×640 JPEG
    └── test/     ←   659 × 640×640 JPEG
```

---

## 2. Data Problem & Solution

### 2.1 The Problem: Partial Annotations

The dataset is a union of multiple source datasets (`source_name` varies per image). Different sources annotate different class subsets:

```
Image 1:  motorbike ✅   helmet ❌   non-helmet ❌   ← source labeled vehicles only
Image 2:  motorbike ❌   helmet ✅   non-helmet ✅   ← source labeled riders only
Image 3:  motorbike ✅   helmet ✅   non-helmet ✅   ← fully labeled
```

Training directly on partial annotations teaches the model to treat unannotated instances as **background**, which corrupts the loss signal and suppresses recall for missing classes.

Fully-labeled images (all 3 classes present) exist in this dataset but are often **low quality**. A single bootstrap model trained only on that subset produces unreliable pseudo-labels.

### 2.2 The Solution: Per-Class Specialist Pseudo-Labeling

Train **three single-class YOLOv8s specialists** — one per class. Each specialist learns from **all images where that class was manually labeled**, regardless of whether other classes are present on the same image.

| Specialist   | Trained on                         | Used to fill in              |
|--------------|------------------------------------|------------------------------|
| `motorbike`  | Images with motorbike boxes        | Missing motorbike labels     |
| `helmet`     | Images with helmet boxes           | Missing helmet labels        |
| `non-helmet` | Images with non-helmet boxes       | Missing non-helmet labels    |

Pseudo-labeling runs the **matching specialist** for each missing class on each partial image. Predictions with score ≥ 0.4 are accepted; manual labels always win on overlap during merge (NMS IoU = 0.5).

### 2.3 End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 0 — Data Pipeline  (data_pipeline.ipynb)                 │
│                                                                 │
│  instances_train.json                                           │
│       ↓                                                         │
│  audit.py              → coverage report, missing_per_image   │
│       ↓                                                         │
│  bootstrap_train.py    → 3 specialist YOLOv8s checkpoints       │
│       ↓                                                         │
│  pseudo_label.py       → pseudo_labels.json                     │
│       ↓                                                         │
│  merge_annotations.py  → instances_train_merged.json            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1 — Model Training  (faster-rcnn / yolo / rtdetr .ipynb) │
│                                                                 │
│  train_fasterrcnn.py   → fasterrcnn_best.pth + results.json     │
│  train_yolo.py         → yolo_best.pt        + results.json     │
│  train_rtdetr.py       → rtdetr_best.pt      + results.json     │
└─────────────────────────────────────────────────────────────────┘
```

Training scripts use `instances_train_merged.json` when it exists; otherwise they fall back to `instances_train.json`.

---

## 3. Models

Three architectures representing different detection paradigms:

| Model                  | Type              | Approx. FPS | COCO mAP@0.5:0.95 |
|------------------------|-------------------|------------:|------------------:|
| YOLOv8m                | Single-stage CNN  |        ~120 |             ~50.2 |
| Faster R-CNN (R50-FPN) | Two-stage CNN     |         ~15 |             ~46.7 |
| RT-DETR-L              | Transformer       |        ~100 |             ~53.4 |

|                        | YOLOv8m            | Faster R-CNN       | RT-DETR-L          |
|------------------------|--------------------|--------------------|--------------------|
| Training API           | Ultralytics        | torchvision        | Ultralytics        |
| Default weights        | `yolov8m.pt`       | ResNet50-FPN COCO  | `rtdetr-l.pt`      |
| Entry-point script     | `train_yolo.py`    | `train_fasterrcnn.py` | `train_rtdetr.py` |
| Kaggle notebook        | `yolo.ipynb`       | `faster-rcnn.ipynb`   | `rtdetr.ipynb`     |

---

## 4. Project Structure

```
train/
├── PLAN.md
├── pyproject.toml              ← uv dependencies
│
├── utils.py                    ← set_seed, get_paths (reads DATA_PATH from env)
├── dataset.py                  ← CocoDetectionDataset, coco_to_yolo_labels, write_dataset_yaml
├── metrics.py                  ← evaluate_coco, measure_fps
│
├── data_pipeline/
│   ├── audit.py                ← Step 1: annotation coverage audit
│   ├── bootstrap_train.py      ← Step 2: train per-class YOLOv8s specialists
│   ├── pseudo_label.py         ← Step 3: pseudo-label missing classes
│   └── merge_annotations.py    ← Step 4: merge + NMS → instances_train_merged.json
│
├── train_fasterrcnn.py         ← Faster R-CNN training entry point
├── train_yolo.py               ← YOLOv8 training entry point
├── train_rtdetr.py             ← RT-DETR training entry point
│
├── data_pipeline.ipynb         ← Kaggle: setup + run all 4 pipeline steps
├── faster-rcnn.ipynb           ← Kaggle: setup + run train_fasterrcnn.py
├── yolo.ipynb                  ← Kaggle: setup + run train_yolo.py
└── rtdetr.ipynb                ← Kaggle: setup + run train_rtdetr.py
```

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
  "pandas",
]
```

### 5.2 Local

```bash
cd train/
uv sync

# Phase 0 — data pipeline (optional, run once)
uv run python data_pipeline/audit.py
uv run python data_pipeline/bootstrap_train.py
uv run python data_pipeline/pseudo_label.py
uv run python data_pipeline/merge_annotations.py

# Phase 1 — model training
uv run python train_fasterrcnn.py
uv run python train_yolo.py
uv run python train_rtdetr.py
```

### 5.3 Path Resolution (`utils.get_paths`)

### 5.3 Path Resolution

Set `DATA_PATH` in a **Config** cell in your notebook (before running any `!uv run` commands):

```python
import os

DATA_PATH = "/kaggle/input/your-dataset-slug"  # edit this
os.environ["DATA_PATH"] = DATA_PATH
```

| Variable      | Local       | Kaggle |
|---------------|-------------|--------|
| Input dataset | `../data`   | `DATA_PATH` (you set in notebook) |
| `data_root`   | `../data`   | `/kaggle/working/data` (writable copy; images symlinked from `DATA_PATH`) |
| `out_root`    | `./output`  | `/kaggle/working` |

After Phase 0, the merged train file is at `/kaggle/working/data/annotations/instances_train_merged.json`.

---

## 6. Kaggle Notebooks

All notebooks share the same setup cells (clone repo → install uv → pin Python 3.13 → write `pyproject.toml` → `uv sync`). Only the final run cells differ.

### 6.1 Common Setup

```python
GITHUB_USER = 'tadtd'
REPO_NAME   = 'intro2ml-helmet-violation-detection'
BRANCH      = 'main'

from kaggle_secrets import UserSecretsClient
GITHUB_TOKEN = UserSecretsClient().get_secret("GITHUB_TOKEN")

# Config cell (after uv sync):
import os
DATA_PATH = "/kaggle/input/your-dataset-slug"  # edit this
os.environ["DATA_PATH"] = DATA_PATH

!git clone --single-branch --branch {BRANCH} \
    https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git
%cd {REPO_NAME}

!apt-get install -y poppler-utils -q
!pip install uv -q
!uv python install 3.13 && uv python pin 3.13
!rm -rf pyproject.toml uv.lock .python-version

# %%writefile pyproject.toml  (content from section 5.1)
!uv sync
```

### 6.2 Run Cells (per notebook)

**`data_pipeline.ipynb`** — run Phase 0:

```bash
!uv run python models/data_pipeline/audit.py
!uv run python models/data_pipeline/bootstrap_train.py
!uv run python models/data_pipeline/pseudo_label.py
!uv run python models/data_pipeline/merge_annotations.py
```

**`faster-rcnn.ipynb`** / **`yolo.ipynb`** / **`rtdetr.ipynb`** — run Phase 1:

```bash
!uv run python models/train_fasterrcnn.py
!uv run python models/train_yolo.py
!uv run python models/train_rtdetr.py
```

---

## 7. Data Pipeline (Phase 0)

### Step 1 — `data_pipeline/audit.py`

- Loads `instances_train.json` via `pycocotools.COCO`
- For each image, records which of `{motorbike, helmet, non-helmet}` have at least one box
- Prints a coverage table to stdout
- Saves to `out_root/audit/`:

| File | Contents |
|------|----------|
| `coverage.csv` | `image_id, file_name, has_motorbike, has_helmet, has_non_helmet, is_fully_labeled` |
| `fully_labeled_ids.json` | Image IDs with all 3 classes |
| `partial_ids.json` | Image IDs missing at least one class |
| `missing_per_image.json` | `{image_id: ["helmet", "non-helmet"]}` |

If all images are fully labeled, subsequent steps are skipped.

### Step 2 — `data_pipeline/bootstrap_train.py`

Trains three **single-class YOLOv8s** specialists (not a single 3-class bootstrap model):

1. For each class, build a COCO subset containing only images + boxes for that class
2. Convert to YOLO labels (`data_root/labels/specialist_{class}/`)
3. Train `YOLOv8s` for 50 epochs, `imgsz=640`, `batch=16`

Outputs:

```
out_root/specialists/
├── motorbike/weights/best.pt
├── helmet/weights/best.pt
├── non_helmet/weights/best.pt
└── manifest.json              ← maps class name → checkpoint path
```

Also writes per-class annotation files: `data/annotations/instances_train_{class}.json`

### Step 3 — `data_pipeline/pseudo_label.py`

- Loads specialist checkpoints from `manifest.json`
- For each partial image, for each **missing class**, runs the matching specialist
- Keeps predictions with `score ≥ 0.4`; discards below

| Score       | Action              |
|-------------|---------------------|
| `≥ 0.6`     | Accept (high)       |
| `0.4 – 0.6` | Accept (medium)     |
| `< 0.4`     | Discard             |

Outputs:

| File | Location |
|------|----------|
| `pseudo_labels.json` | `data/annotations/` |
| `pseudo_label_scores.csv` | `out_root/audit/` |

### Step 4 — `data_pipeline/merge_annotations.py`

1. Load `instances_train.json` (manual) + `pseudo_labels.json` (auto)
2. Pool annotations per `(image_id, category_id)`
3. NMS at IoU = 0.5 — **manual boxes always win** over pseudo boxes on overlap
4. Assign new sequential annotation IDs
5. Write `data/annotations/instances_train_merged.json`

---

## 8. Shared Modules

### `utils.py`

| Function | Description |
|----------|-------------|
| `set_seed(seed=42)` | Seeds `random`, `numpy`, `torch`, CUDA |
| `get_paths(dataset_slug)` | Returns `(data_root, out_root)` with Kaggle auto-detection |

### `dataset.py`

| Symbol | Description |
|--------|-------------|
| `CocoDetectionDataset(ann_json, img_dir)` | PyTorch `Dataset` for Faster R-CNN. Returns `(image_tensor, target_dict)` with keys `boxes` (xyxy), `labels`, `image_id`, `area`, `iscrowd`. Includes `collate_fn`. |
| `coco_to_yolo_labels(ann_json, data_root, split, force=False)` | Writes YOLO `.txt` labels to `data_root/labels/{split}/`. Normalised `cx cy w h`. Idempotent unless `force=True`. |
| `write_dataset_yaml(yaml_path, data_root, nc, names)` | Writes Ultralytics `dataset.yaml`. |

### `metrics.py`

| Function | Description |
|----------|-------------|
| `evaluate_coco(gt_ann_json, predictions)` | COCOeval wrapper. Returns `{"mAP50", "mAP50_95", "AR100"}`. |
| `measure_fps(model_fn, dummy_input, warmup=10, runs=100)` | Inference throughput in FPS. |

---

## 9. Model Training (Phase 1)

All three scripts:
- Pick `instances_train_merged.json` if present, else `instances_train.json`
- Evaluate on **val** and **test** (never modified)
- Save checkpoint + `*_results.json` to `out_root`

### `train_fasterrcnn.py`

| Config constant | Value |
|-----------------|-------|
| `EPOCHS`        | 50    |
| `BATCH_SIZE`    | 4     |
| `LR`            | 1e-3  |
| `MOMENTUM`      | 0.9   |
| `WEIGHT_DECAY`  | 5e-4  |
| `LR_STEP`       | 10    |
| `LR_GAMMA`      | 0.1   |

Model: `fasterrcnn_resnet50_fpn(weights="DEFAULT")` with `FastRCNNPredictor` head replaced for 4 classes (background + 3). Optimiser: SGD + StepLR. Best checkpoint saved by val loss.

### `train_yolo.py`

| Config constant | Value        |
|-----------------|--------------|
| `MODEL`         | `yolov8m.pt` |
| `EPOCHS`        | 50           |
| `BATCH`         | 16           |
| `IMGSZ`         | 640          |
| `LR0`           | 1e-3         |
| `LRF`           | 0.01         |
| `MOMENTUM`      | 0.937        |
| `WEIGHT_DECAY`  | 5e-4         |

Converts COCO → YOLO labels, trains via `YOLO(MODEL).train(...)`, evaluates with `model.val()`.

### `train_rtdetr.py`

Same structure as `train_yolo.py`. Differs only in config:

| Config constant | Value        |
|-----------------|--------------|
| `MODEL`         | `rtdetr-l.pt` |
| `BATCH`         | 8            |
| `LR0`           | 1e-4         |

Uses `RTDETR(MODEL)` instead of `YOLO(MODEL)`.

---

## 10. Outputs

### Data pipeline

```
out_root/audit/
├── coverage.csv
├── fully_labeled_ids.json
├── partial_ids.json
├── missing_per_image.json
└── pseudo_label_scores.csv

out_root/specialists/
├── motorbike/weights/best.pt
├── helmet/weights/best.pt
├── non_helmet/weights/best.pt
└── manifest.json

data/annotations/
├── pseudo_labels.json
└── instances_train_merged.json     ← final training annotation file
```

### Model training

```
out_root/
├── fasterrcnn_best.pth
├── fasterrcnn_results.json
├── yolo_best.pt
├── yolo_results.json
├── rtdetr_best.pt
└── rtdetr_results.json
```

Each `*_results.json`:

```json
{
  "val":  {"mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0},
  "test": {"mAP50": 0.0, "mAP50_95": 0.0, "AR100": 0.0},
  "fps":  0.0
}
```

---

## 11. Key Design Decisions

- **Per-class specialists, not fully-labeled bootstrap.** Fully-labeled images are low quality in this dataset. Each class gets its own single-class detector trained on all images where that class is manually labeled.
- **Val and test never modified.** Pseudo-labeling only touches the train set. Evaluation sets stay human-annotated.
- **Images pre-letterboxed at 640×640.** `IMGSZ=640` is hardcoded; no resize transform needed.
- **NMS priority: manual wins.** Human annotations are ground truth; pseudo-labels are discarded on IoU > 0.5 overlap.
- **Automatic threshold acceptance.** All pseudo-labels with score ≥ 0.4 are accepted (no human review step on Kaggle).
- **Merged annotation fallback.** Training scripts auto-detect `instances_train_merged.json`; if the data pipeline was not run, training proceeds on the original file.
- **`uv` for dependency management.** `pyproject.toml` + `uv sync` + `uv run python <script>`. Notebooks are thin wrappers that set up the environment and call scripts.
- **Multi-file, not monolithic.** Shared logic in `utils.py`, `dataset.py`, `metrics.py`. One entry-point script per model. Data pipeline split into 4 focused scripts.
