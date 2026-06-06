# Helmet Violation Detection — Training Plan

Object detection pipeline for helmet violation on motorbikes. Three detectors are trained and compared: **YOLOv8m**, **Faster R-CNN (ResNet50-FPN)**, and **RT-DETR-L**. All code lives under `models/`, runs with **`uv`**, and is designed to execute on **Kaggle** via thin Jupyter notebooks that call Python scripts.

---

## 1. Dataset

The dataset lives in `data/` (see [`data/README.md`](../data/README.md)). Annotations are **COCO JSON**; images are pre-letterboxed to **640×640**.

### Classes

| id | name         | supercategory |
|----|--------------|---------------|
| 1  | `motorbike`  | vehicle       |
| 2  | `helmet`     | safety        |
| 3  | `non-helmet` | violation     |

### Splits

| Split | Images | Annotations | Annotation file |
|-------|-------:|------------:|-----------------|
| train |  2,309 |      11,047 | `instances_train_merged.json` |
| val   |    330 |       1,889 | `instances_val.json` |
| test  |    659 |       1,861 | `instances_test.json` |

The train set was built from multiple sources with **partial annotations** (not every class labeled on every image). The merged train file combines manual labels with pseudo-labels so all three classes are covered. **Val and test are never modified.**

```
data/
├── annotations/
│   ├── instances_train.json          ← original manual labels (kept for reference)
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

## 3. Project Structure

```
models/
├── PLAN.md
├── pyproject.toml              ← uv dependencies
│
├── utils.py                    ← set_seed, get_paths, get_train_ann_path
├── dataset.py                  ← CocoDetectionDataset, coco_to_yolo_labels, write_dataset_yaml
├── metrics.py                  ← evaluate_coco, measure_fps
│
├── train_fasterrcnn.py         ← Faster R-CNN training entry point
├── train_yolo.py               ← YOLOv8 training entry point
├── train_rtdetr.py             ← RT-DETR training entry point
│
├── faster-rcnn.ipynb           ← Kaggle: setup + run train_fasterrcnn.py
├── yolo.ipynb                  ← Kaggle: setup + run train_yolo.py
└── rtdetr.ipynb                ← Kaggle: setup + run train_rtdetr.py
```

---

## 4. Setup

### 4.1 Dependencies (`pyproject.toml`)

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
]
```

### 4.2 Local

```bash
cd models/
uv sync

uv run python train_fasterrcnn.py
uv run python train_yolo.py
uv run python train_rtdetr.py
```

Data is read from `../data/` automatically.

### 4.3 Path Resolution

Set `DATA_PATH` and `MPLBACKEND` in a **Config** cell in your notebook (before running any `!uv run` commands):

```python
import os

DATA_PATH = "/kaggle/input/your-dataset-slug"  # edit this
os.environ["DATA_PATH"] = DATA_PATH
os.environ["MPLBACKEND"] = "Agg"  # required when running scripts via !uv run from notebook
```

| Variable      | Local       | Kaggle |
|---------------|-------------|--------|
| Input dataset | `../data`   | `DATA_PATH` (you set in notebook) |
| `data_root`   | `../data`   | `/kaggle/working/data` (writable copy; images symlinked from `DATA_PATH`) |
| `out_root`    | `./output`  | `/kaggle/working` |

On Kaggle, annotation files (including `instances_train_merged.json`) are copied from `DATA_PATH` into `/kaggle/working/data/annotations/`.

---

## 5. Kaggle Notebooks

All notebooks share the same setup cells (clone repo → install uv → pin Python 3.13 → write `pyproject.toml` → `uv sync`). Only the final run cell differs.

### 5.1 Common Setup

```python
GITHUB_USER = 'tadtd'
REPO_NAME   = 'intro2ml-helmet-violation-detection'
BRANCH      = 'main'

from kaggle_secrets import UserSecretsClient
GITHUB_TOKEN = UserSecretsClient().get_secret("GITHUB_TOKEN")

!git clone --single-branch --branch {BRANCH} \
    https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{REPO_NAME}.git
%cd {REPO_NAME}

!apt-get install -y poppler-utils -q
!pip install uv -q
!uv python install 3.13 && uv python pin 3.13
!rm -rf pyproject.toml uv.lock .python-version

# %%writefile pyproject.toml  (content from section 4.1)
!uv sync
```

Config cell:

```python
import os

DATA_PATH = "/kaggle/input/your-dataset-slug"  # edit this
os.environ["DATA_PATH"] = DATA_PATH
os.environ["MPLBACKEND"] = "Agg"
```

### 5.2 Run Cells

```bash
!uv run python models/train_fasterrcnn.py
!uv run python models/train_yolo.py
!uv run python models/train_rtdetr.py
```

---

## 6. Shared Modules

### `utils.py`

| Function | Description |
|----------|-------------|
| `set_seed(seed=42)` | Seeds `random`, `numpy`, `torch`, CUDA |
| `get_paths()` | Returns `(data_root, out_root)` with Kaggle auto-detection |
| `get_train_ann_path(data_root)` | Returns `instances_train_merged.json` if present, else `instances_train.json` |

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

## 7. Model Training

All three scripts:
- Train on `instances_train_merged.json` (or fallback)
- Evaluate on **val** and **test**
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

## 8. Outputs

```
out_root/   (models/output/ locally, /kaggle/working/ on Kaggle)
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

Use the checkpoint with the best test metrics for deployment.

---

## 9. Key Design Decisions

- **Pre-merged train annotations.** Partial-label problem is handled offline; `models/` only trains detectors on the ready-made `instances_train_merged.json`.
- **Val and test never modified.** Evaluation sets stay human-annotated.
- **Images pre-letterboxed at 640×640.** `IMGSZ=640` is hardcoded; no resize transform needed.
- **Merged annotation fallback.** If `instances_train_merged.json` is missing, training proceeds on `instances_train.json`.
- **`uv` for dependency management.** `pyproject.toml` + `uv sync` + `uv run python <script>`. Notebooks are thin wrappers that set up the environment and call scripts.
- **Multi-file, not monolithic.** Shared logic in `utils.py`, `dataset.py`, `metrics.py`. One entry-point script per model.
