# Model ONNX Input/Output Shapes

Generated for Member 2 on 2026-06-25.

## Weights

| Model | Source checkpoint | Backend ONNX | Status |
|---|---|---|---|
| YOLO | `backend/app/weights/yolo_best.pt` | `backend/app/weights/yolo_best.onnx` | Exported |
| RT-DETR | `backend/app/weights/rtdetr_best.pt` | `backend/app/weights/rtdetr_best.onnx` | Exported |
| Faster R-CNN | `backend/app/weights/fasterrcnn_best.pth` | `backend/app/weights/fasterrcnn_best.onnx` | Exported |

Checkpoints were downloaded from Hugging Face repo `dtdat1234/helmet-violation-detection-models` following `models/checkpoints/README.md`.

Export was run from the `models/` environment because it contains the heavier training/export dependencies (`torch`, `torchvision`, `ultralytics`, `onnx`, `onnxsim`, `onnxscript`). Backend runtime inference only needs ONNX Runtime, OpenCV, and NumPy once `.onnx` files exist.

## YOLO

- Export tool: Ultralytics `YOLO.export`
- Opset: 12
- Input name: `images`
- Input shape: `[1, 3, 640, 640]`
- Input type: `tensor(float)`
- Output name: `output0`
- Output shape: `[1, 300, 6]`
- Output type: `tensor(float)`
- Output format: `[x1, y1, x2, y2, confidence, class_id]` in 640x640 letterboxed image pixels.

## RT-DETR

- Export tool: Ultralytics `RTDETR.export`
- Opset: 16
- Reason for opset 16: opset 12 failed because `aten::grid_sampler` support starts at opset 16.
- Input name: `images`
- Input shape: `[1, 3, 640, 640]`
- Input type: `tensor(float)`
- Output name: `output0`
- Output shape: `[1, 300, 6]`
- Output type: `tensor(float)`
- Output format: `[cx, cy, w, h, confidence, class_id]` normalized to the 640x640 model input.

## Faster R-CNN

- Export tool: Torch ONNX legacy TorchScript exporter (`dynamo=False`)
- Opset: 16 requested
- New Torch exporter issue: `torch.export` failed on data-dependent `torchvision.ops.batched_nms`; legacy exporter succeeded.
- Input name: `images`
- Input shape: `[1, 3, 640, 640]`
- Input type: `tensor(float)`
- Outputs:
  - `boxes`: shape `['Concatboxes_dim_0', 4]`, type `tensor(float)`
  - `labels`: shape `['Gatherlabels_dim_0']`, type `tensor(int64)`
  - `scores`: shape `['Gatherlabels_dim_0']`, type `tensor(float)`

## Class Mapping

YOLO and RT-DETR:

```text
0 -> motorbike
1 -> helmet
2 -> non-helmet
```

Faster R-CNN:

```text
1 -> motorbike
2 -> helmet
3 -> non-helmet
```

## CPU FPS Benchmark

Image: `image.png`
Device: CPU, AMD Ryzen 9 6900HS with Radeon Graphics
Command pattern:

```bash
cd backend
uv run python scripts/benchmark_fps.py --model <model> --image ../image.png --warmup 1 --runs 3
```

| Model | Runs | Elapsed | FPS |
|---|---:|---:|---:|
| YOLO | 3 | 0.716s | 4.19 |
| RT-DETR | 3 | 1.077s | 2.79 |
| Faster R-CNN | 3 | 2.968s | 1.01 |

## Smoke Test Outputs

Generated files:

- `backend/outputs/yolo_smoke.jpg`
- `backend/outputs/rtdetr_smoke.jpg`
- `backend/outputs/fasterrcnn_smoke.jpg`
- `backend/outputs/sample_video.mp4`
- `backend/outputs/yolo_video_smoke.mp4`
- `backend/outputs/rtdetr_video_smoke.mp4`
- `backend/outputs/fasterrcnn_video_smoke.mp4`

Commands:

```bash
cd backend
uv run python scripts/test_inference_image.py --model yolo --image ../image.png --out outputs/yolo_smoke.jpg
uv run python scripts/test_inference_image.py --model rtdetr --image ../image.png --out outputs/rtdetr_smoke.jpg
uv run python scripts/test_inference_image.py --model fasterrcnn --image ../image.png --out outputs/fasterrcnn_smoke.jpg
uv run python scripts/test_inference_video.py --model yolo --video outputs/sample_video.mp4 --out outputs/yolo_video_smoke.mp4 --max-frames 5 --every-n 2
uv run python scripts/test_inference_video.py --model rtdetr --video outputs/sample_video.mp4 --out outputs/rtdetr_video_smoke.mp4 --max-frames 5 --every-n 2
uv run python scripts/test_inference_video.py --model fasterrcnn --video outputs/sample_video.mp4 --out outputs/fasterrcnn_video_smoke.mp4 --max-frames 5 --every-n 2
```

Manual visual check:

- YOLO boxes align with helmets and one motorbike; no coordinate scaling issue observed.
- RT-DETR boxes align with helmets; one non-helmet false positive is model quality, not wrapper scaling.
- Faster R-CNN boxes align spatially but produce several low-confidence non-helmet false positives.

## Docker Worker Verification

Worker Docker image was built and checked with:

```bash
cd backend
docker build -f Dockerfile.worker -t helmet-worker-member2-check .
docker run --rm helmet-worker-member2-check python -c "from pathlib import Path; import cv2, numpy, onnxruntime; from app.models import run_inference; weights=Path('/app/app/weights'); print('imports ok'); print(sorted(p.name for p in weights.glob('*.onnx')))"
```

Result:

```text
imports ok
['fasterrcnn_best.onnx', 'rtdetr_best.onnx', 'yolo_best.onnx']
```
