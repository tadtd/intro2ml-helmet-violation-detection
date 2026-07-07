from .base import Detection


def run_inference(*args, **kwargs):
    from .registry import run_inference as _run_inference

    return _run_inference(*args, **kwargs)


__all__ = ["Detection", "run_inference"]
