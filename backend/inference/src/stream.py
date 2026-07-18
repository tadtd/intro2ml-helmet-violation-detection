"""Live-stream detection websocket.

Runs the ONNX model over any OpenCV-readable source (a looped demo file, an RTSP
camera, or an HLS `.m3u8` feed) and pushes annotated JPEG frames to the browser.

This reuses the inference image, which already carries onnxruntime, opencv, the
model weights and the detection code, so no model or weight is duplicated. It is
served by a separate compose service that runs uvicorn instead of the Celery
worker, keeping the realtime workload off the batch queue.
"""

import asyncio
import logging
import os
from pathlib import Path

import cv2

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from common.config import get_settings
from .models.base import Detection
from .models.registry import run_inference
from .violation_logic import find_violations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference.stream")

settings = get_settings()

app = FastAPI(title="Realtime Detection Stream")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DEMO_DIR = Path(__file__).resolve().parents[1] / "demo"

# Named sources the operator can pick without typing a URL. A source can also be
# any RTSP/HLS/http URL passed verbatim via `?src=`.
NAMED_SOURCES: dict[str, str] = {
    "demo-violation": str(_DEMO_DIR / "violation_demo.mp4"),
    "demo-traffic": str(_DEMO_DIR / "traffic_sample.mp4"),
    # The three dashboard locations map to demo clips until a real feed URL is
    # supplied; override any of these with CAMERA_SRC_<ID> env vars.
    "cam-01": os.getenv("CAMERA_SRC_CAM_01", str(_DEMO_DIR / "traffic_sample.mp4")),
    "cam-02": os.getenv("CAMERA_SRC_CAM_02", str(_DEMO_DIR / "violation_demo.mp4")),
    "cam-03": os.getenv("CAMERA_SRC_CAM_03", str(_DEMO_DIR / "traffic_sample.mp4")),
}

DEFAULT_SOURCE = str(_DEMO_DIR / "violation_demo.mp4")
DEFAULT_MODEL = "yolo"

# Accept either the model id (yolo) or the stored display name (YOLO, RT-DETR).
_MODEL_ALIASES = {
    "yolo": "yolo",
    "rtdetr": "rtdetr",
    "rt-detr": "rtdetr",
    "fasterrcnn": "fasterrcnn",
    "faster r-cnn": "fasterrcnn",
    "faster-r-cnn": "fasterrcnn",
}


def _normalize_model(value: str | None) -> str:
    return _MODEL_ALIASES.get((value or "").strip().lower(), DEFAULT_MODEL)
TARGET_FPS = 12
DETECT_EVERY = 3  # run the model on 1 of every N frames; reuse boxes in between

_COLOURS = {
    "motorbike": (0, 200, 0),
    "helmet": (255, 180, 0),
    "non-helmet": (0, 0, 255),
}


def _is_youtube(url: str) -> bool:
    return "youtube.com/" in url or "youtu.be/" in url


def _resolve_youtube(url: str) -> str:
    """Resolve a YouTube (live or recorded) URL to a direct stream URL for OpenCV.

    A live stream resolves to its HLS manifest; a recorded video to a direct
    progressive URL. Both are readable by cv2.VideoCapture.
    """
    import yt_dlp

    options = {
        "quiet": True,
        "no_warnings": True,
        "format": "best[protocol^=http][height<=720]/best[height<=720]/best",
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    stream_url = info.get("url")
    if not stream_url:
        raise ValueError(f"Could not resolve a stream URL from {url}")
    return stream_url


def _resolve_source(raw: str | None) -> str:
    if not raw:
        return DEFAULT_SOURCE
    if raw in NAMED_SOURCES:
        return NAMED_SOURCES[raw]
    if _is_youtube(raw):
        return _resolve_youtube(raw)
    # A verbatim URL (rtsp://, http(s)://…m3u8) or file path.
    return raw


def _is_loopable_file(source: str) -> bool:
    return "://" not in source and Path(source).is_file()


def _draw(frame, detections: list[Detection], violation_boxes: set[tuple]) -> None:
    for det in detections:
        x1, y1, x2, y2 = (int(v) for v in det.box)
        is_violation = det.box in violation_boxes
        colour = (0, 0, 255) if is_violation else _COLOURS.get(det.class_name, (200, 200, 200))
        thickness = 3 if is_violation else 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, thickness)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(
            frame, label, (x1, max(y1 - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2,
        )


async def _stream(websocket: WebSocket, source: str, model_name: str) -> None:
    loop = asyncio.get_event_loop()
    capture = await loop.run_in_executor(None, cv2.VideoCapture, source)
    if not capture.isOpened():
        await websocket.send_json({"type": "error", "message": f"Cannot open source: {source}"})
        return

    loopable = _is_loopable_file(source)
    frame_period = 1.0 / TARGET_FPS
    frame_idx = 0
    detections: list[Detection] = []
    violation_boxes: set[tuple] = set()

    try:
        while True:
            ok, frame = await loop.run_in_executor(None, capture.read)
            if not ok:
                if loopable:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break  # a live feed that dropped: stop and let the client reconnect

            if frame_idx % DETECT_EVERY == 0:
                detections = await loop.run_in_executor(None, run_inference, frame, model_name)
                violations = find_violations(detections)
                # A violation may have no motorbike attached, so guard against None.
                violation_boxes = {v.non_helmet.box for v in violations}
                violation_boxes |= {v.motorbike.box for v in violations if v.motorbike is not None}
                await websocket.send_json(
                    {
                        "type": "stats",
                        "detections": len(detections),
                        "violations": len(violations),
                    }
                )

            _draw(frame, detections, violation_boxes)
            ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                await websocket.send_bytes(buffer.tobytes())

            frame_idx += 1
            await asyncio.sleep(frame_period)
    finally:
        capture.release()


@app.websocket("/ws/camera")
async def camera_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    raw_source = websocket.query_params.get("id") or websocket.query_params.get("src")
    model_name = _normalize_model(websocket.query_params.get("model"))
    try:
        # Resolving a YouTube URL hits the network, so keep it off the event loop.
        loop = asyncio.get_event_loop()
        source = await loop.run_in_executor(None, _resolve_source, raw_source)
    except Exception as exc:
        logger.error("Could not resolve source %s: %s", raw_source, exc)
        await websocket.send_json({"type": "error", "message": f"Không mở được nguồn: {exc}"})
        return

    logger.info("Live detection stream opened: source=%s model=%s", source[:80], model_name)
    try:
        await _stream(websocket, source, model_name)
    except WebSocketDisconnect:
        logger.info("Live detection stream disconnected")
    except Exception as exc:
        logger.error("Live detection stream error: %s", exc)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "realtime"}
