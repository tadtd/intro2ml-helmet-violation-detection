# Helmet Violation Detection – Crawl Agent

Crawl YouTube for Vietnamese traffic videos, extract frames, and use **Ollama LLaVA** (vision LLM) to collect images of **people not wearing helmets**.

## Quick Start (Kaggle)

1. **Upload** `config.py`, `crawler.py`, and `helmet_crawler.ipynb` to a new Kaggle notebook.
2. In notebook settings enable **GPU (T4)** and **Internet**.
3. Run all cells – the notebook installs `uv`, dependencies, and Ollama automatically.

## How It Works

```
YouTube search  →  yt-dlp download  →  OpenCV frame extraction  →  Ollama LLaVA  →  saved images
```

### Two-stage detection


| Stage | Purpose           | Prompt                                                               |
| ----- | ----------------- | -------------------------------------------------------------------- |
| 1     | Quick pre-filter  | *"Does this image show any person … NOT wearing a helmet? YES / NO"* |
| 2     | Detailed analysis | Returns JSON with position, activity, and confidence per violation   |


Only frames that pass Stage 1 (YES) are sent to Stage 2. Frames with at least one medium/high-confidence violation are saved.

## Project Files


| File                   | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `helmet_crawler.ipynb` | Kaggle notebook – primary entry point             |
| `crawler.py`           | Core module (download, extract, detect, pipeline) |
| `config.py`            | All tuneable settings                             |
| `main.py`              | CLI entry point (`uv run main.py`)                |


## Configuration

Edit `config.py` or override at runtime in the notebook. Key settings:


| Setting               | Default    | Description                                 |
| --------------------- | ---------- | ------------------------------------------- |
| `OLLAMA_MODEL`        | `llava:7b` | Vision model                                |
| `SEARCH_QUERIES`      | 6 queries  | YouTube search terms (Vietnamese + English) |
| `MAX_VIDEOS_TOTAL`    | 10         | Max videos to download                      |
| `FRAME_INTERVAL`      | 2          | Seconds between extracted frames            |
| `DUPLICATE_THRESHOLD` | 10         | dhash hamming distance for dedup            |
| `TWO_STAGE_DETECTION` | True       | Enable quick pre-filter                     |


## Output

- `output/no_helmet/` – violation images named `{video_id}_{timestamp}s.jpg`
- `output/results.csv` – all detections with video ID, timestamp, violation count, and JSON details
- `output/violations_grid.png` – matplotlib grid of top detections

## Local Usage

```bash
# Requires Ollama running locally with llava:7b pulled
uv run main.py
```

## CVAT Bounding Box Correction Workflow

Use these scripts to review and correct incomplete bounding boxes in CVAT, then merge the corrected annotations back into split COCO files.

### 1. Prepare a single CVAT task bundle

```bash
python scripts/prepare_cvat_coco_task.py \
	--dataset-root data/processed/helmet_violation_coco \
	--output-root data/processed/cvat_round1 \
	--overwrite
```

Outputs:

- `data/processed/cvat_round1/images/` (all images with split/id-prefixed names)
- `data/processed/cvat_round1/annotations/instances_all_for_cvat.json`
- `data/processed/cvat_round1/cvat_upload_bundle.zip`

### 2. Annotate in CVAT

1. Create a new object detection task.
2. Upload all files in `data/processed/cvat_round1/images/`.
3. Import annotations using COCO from `instances_all_for_cvat.json`.
4. Fix incomplete boxes and save.
5. Export annotations as COCO 1.0 JSON.

### 3. Merge corrected annotations back to train/val/test

```bash
python scripts/merge_cvat_coco_back.py \
	--dataset-root data/processed/helmet_violation_coco \
	--cvat-coco path/to/cvat_export.json
```

What this does:

- Backs up current split annotations under `data/processed/helmet_violation_coco/annotations/backup_before_cvat_merge_*`
- Rewrites:
	- `data/processed/helmet_violation_coco/annotations/instances_train.json`
	- `data/processed/helmet_violation_coco/annotations/instances_val.json`
	- `data/processed/helmet_violation_coco/annotations/instances_test.json`
- Writes merge report to `data/processed/helmet_violation_coco/reports/cvat_merge_report.json`

