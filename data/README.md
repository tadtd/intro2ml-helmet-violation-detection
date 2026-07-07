Download the dataset from [here](https://drive.google.com/drive/folders/1BxIzH9uT9LtXADpFVpZjoWGRMSw-hhbG) and put it in the `data` folder.

# Folder structure

```
data/
├── annotations/
│   ├── instances_train.json          ← original manual labels
│   ├── instances_train_merged.json   ← training file (manual + pseudo-labels)
│   ├── instances_val.json
│   ├── instances_test.json
│   └── pseudo_labels.json            ← optional, auto-generated labels only
└── images/
    ├── train/    ← 2,309 × 640×640 JPEG
    ├── val/      ←   330 × 640×640 JPEG
    └── test/     ←   659 × 640×640 JPEG
```

# Classes

| id | name         |
|----|--------------|
| 1  | `motorbike`  |
| 2  | `helmet`     |
| 3  | `non-helmet` |

# Splits

| Split | Images | Annotations | File |
|-------|-------:|------------:|------|
| train |  2,309 |      10,358 | `instances_train_merged.json` |
| val   |    330 |       14797 | `instances_val.json` |
| test  |    659 |       2960 | `instances_test.json` |

Training scripts in `models/` use **`instances_train_merged.json`** when present (falls back to `instances_train.json`). Val and test always use their original annotation files.

# Format

- **COCO JSON** — bounding boxes in pixel-space `[x, y, w, h]` (top-left origin)
- Images are pre-letterboxed to **640×640** (grey padding RGB 114)
- Do not modify `images/` or val/test annotations
