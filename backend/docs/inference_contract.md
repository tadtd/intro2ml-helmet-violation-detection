# Inference Contract

Member 2 exposes one stable function for backend routes, Celery workers, and WebSocket frame handling.

## Import

```python
from app.models import Detection, run_inference
```

## Function

```python
detections = run_inference(image, model_name)
```

## Input

- `image`: OpenCV BGR `np.ndarray`, shape `[H, W, 3]`.
- `model_name`: one of `"yolo"`, `"rtdetr"`, `"fasterrcnn"`.

## Output

Returns `list[Detection]`.

```python
Detection(
    class_name="motorbike",
    box=(10.0, 20.0, 120.0, 180.0),
    confidence=0.92,
    track_id=None,
)
```

## Detection Fields

- `class_name`: `"motorbike"`, `"helmet"`, or `"non-helmet"`.
- `box`: `(x1, y1, x2, y2)` in original image pixel coordinates.
- `confidence`: model confidence in `[0, 1]`.
- `track_id`: optional downstream tracker id. Model wrappers return `None`.

Use `confidence`, not `conf`.

## JSON Conversion

Use `Detection.to_dict()` before sending detections over FastAPI/WebSocket JSON responses.

```python
payload = [det.to_dict() for det in detections]
```

The JSON-ready shape is:

```python
{
    "class_name": det.class_name,
    "box": list(det.box),
    "confidence": det.confidence,
    "track_id": det.track_id,
}
```

## Stub Mode

Set `USE_STUB_INFERENCE=true` to return deterministic fake detections without loading ONNX weights.

```bash
USE_STUB_INFERENCE=true uv run pytest tests/test_inference_contract.py -q
```

## Errors

- Unsupported model names raise `ValueError`.
- Invalid images raise `ValueError`.
- Missing real model weights raise `FileNotFoundError`.
- Runtime model failures raise the underlying ONNX Runtime exception.
