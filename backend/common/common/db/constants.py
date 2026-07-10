from typing import Literal

ModelName = Literal["YOLO", "RT-DETR", "Faster R-CNN"]
VideoStatus = Literal["pending", "processing", "done", "failed"]

MODEL_NAME_BY_API_VALUE: dict[str, ModelName] = {
    "yolo": "YOLO",
    "rtdetr": "RT-DETR",
    "fasterrcnn": "Faster R-CNN",
    "faster-r-cnn": "Faster R-CNN",
    "faster r-cnn": "Faster R-CNN",
}

SUPPORTED_MODEL_VALUES = tuple(MODEL_NAME_BY_API_VALUE.keys())


def normalize_model_name(value: str) -> ModelName:
    """Convert API/user model identifiers to the database enum-like values."""
    normalized = value.strip().lower()
    model_name = MODEL_NAME_BY_API_VALUE.get(normalized)
    if model_name is None:
        allowed = ", ".join(SUPPORTED_MODEL_VALUES)
        raise ValueError(f"model_name must be one of: {allowed}")
    return model_name