from app.models.base import Detection


def run_inference(*args, **kwargs):
    from app.models.registry import run_inference as _run_inference

    return _run_inference(*args, **kwargs)

__all__ = ["Detection", "run_inference"]
