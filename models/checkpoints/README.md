# Model Checkpoints

This directory stores trained model weights for the helmet violation detection
project.

## Available Checkpoints

| File | Model | Description |
| --- | --- | --- |
| `fasterrcnn_best.pth` | Faster R-CNN | Best saved PyTorch checkpoint for the Faster R-CNN helmet violation detector. |

Large checkpoint files are not intended to be versioned directly in Git. The
published model artifacts are available on Hugging Face:

https://huggingface.co/dtdat1234/helmet-violation-detection-models

## Downloading From Hugging Face

Install the Hugging Face CLI if needed:

```bash
pip install -U huggingface_hub
```

Download the model files into this directory:

```bash
huggingface-cli download dtdat1234/helmet-violation-detection-models \
  --local-dir models/checkpoints \
  --local-dir-use-symlinks False
```

If you are already inside `models/checkpoints`, use:

```bash
huggingface-cli download dtdat1234/helmet-violation-detection-models \
  --local-dir . \
  --local-dir-use-symlinks False
```

## Usage

Training and inference scripts should load checkpoints from this directory using
relative paths such as:

```python
checkpoint_path = "models/checkpoints/fasterrcnn_best.pth"
```

Keep this README updated when adding, replacing, or publishing new model
checkpoints.
