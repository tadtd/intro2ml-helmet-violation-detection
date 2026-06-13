# Training Notebooks

This directory contains experimental notebooks used to train and evaluate helmet
violation detection models.

## Contents

| Notebook | Purpose |
| --- | --- |
| `faster-rcnn.ipynb` | Faster R-CNN training and evaluation workflow. |
| `rtdetr.ipynb` | RT-DETR training and evaluation workflow. |
| `yolo26m.ipynb` | YOLO26m training and evaluation workflow. |
| `yolov8.ipynb` | YOLOv8 training and evaluation workflow. |

The notebooks are intended for exploration, experiment tracking, and result
inspection. Reusable training logic should stay in the Python modules under
`models/`, such as `train_fasterrcnn.py`, `train_rtdetr.py`, `train_yolo.py`,
`dataset.py`, and `metrics.py`.

## Model Artifacts

Published checkpoints are hosted on Hugging Face:

https://huggingface.co/dtdat1234/helmet-violation-detection-models

Download the checkpoints before running notebook cells that load trained
weights:

```bash
pip install -U huggingface_hub
huggingface-cli download dtdat1234/helmet-violation-detection-models \
  --local-dir models/checkpoints \
  --local-dir-use-symlinks False
```

## Recommended Workflow

1. Run notebooks from the repository root so relative paths resolve correctly.
2. Keep datasets and checkpoints outside Git when they are large.
3. Move stable training code from notebooks into scripts under `models/`.
4. Use the notebooks for visualization, comparison, and final experiment notes.

## Related Paths

- `models/checkpoints/`: trained model weights.
- `models/best_configs/`: selected training configurations.
- `models/train_fasterrcnn.py`: Faster R-CNN training script.
- `models/train_rtdetr.py`: RT-DETR training script.
- `models/train_yolo.py`: YOLO training script.
