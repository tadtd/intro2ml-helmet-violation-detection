import os
import json
import logging
import cv2
import redis
from celery.exceptions import SoftTimeLimitExceeded

from common.celery import celery_app
from common.config import get_settings
from common.db.storage import get_video_url
from common.db.videos import update_video_status
from common.db.violations import insert_violation
from common.db.storage import upload_crop
from .models.registry import run_inference
from .violation_logic import find_violations
from .tracker import IoUTracker

from .heuristics.motion import is_stationary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference.worker")

settings = get_settings()


@celery_app.task(name="process_video", bind=True)
def process_video(
    self,
    video_id: str,
    storage_path: str,
    filename: str,
    model_name: str,
    user_id: str,
) -> dict[str, str]:
    logger.info(f"Starting processing video {video_id} using model {model_name}")
    try:
        update_video_status(video_id, "processing")
    except Exception as exc:
        logger.error(f"Failed to update video status to processing: {exc}")
        return {"status": "failed", "error": "Database status update failed"}

    # Initialize redis client for events publishing
    try:
        r_client = redis.from_url(settings.redis_url)
    except Exception as exc:
        logger.warning(f"Could not connect to Redis for event publishing: {exc}")
        r_client = None

    if r_client:
        try:
            r_client.publish(
                "job_status_update",
                json.dumps({
                    "jobId": video_id,
                    "fileName": filename,
                    "status": "processing",
                    "modelUsed": model_name
                })
            )
        except Exception as e:
            logger.warning(f"Failed to publish processing status: {e}")

    try:
        video_url = get_video_url(storage_path)
        logger.info(f"Video streaming URL obtained for {storage_path}")

        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            raise ValueError(f"Could not open video URL: {video_url}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info(f"Video metadata: {width}x{height} @ {fps} FPS, {total_frames} frames total")

        from .tracker import iou

        # A single tracker follows each violation by its track_box — the primary
        # rider's head expanded to the whole body. Tracking that (never the
        # motorbike) keeps a rider on one identity whether or not its bike is
        # detected in a given frame, so it does not fragment into a fresh crop each
        # time the bike box flickers. The box is large, so it overlaps well between
        # sampled frames even for a fast rider, and the tracker also matches on the
        # predicted next position — together these keep one person on one track.
        tracker = IoUTracker(iou_threshold=0.25, max_missed=10)
        processed: set[str] = set()
        histories: dict[str, list] = {}

        def _match_track(box, tracks) -> int | None:
            best_id, best_iou = None, 0.0
            for track in tracks:
                score = iou(box, track.box)
                if score > best_iou:
                    best_iou, best_id = score, track.track_id
            return best_id

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every 3rd frame: dense enough to catch brief detections and
            # keep tracking stable, still fast enough on local CPU.
            if frame_idx % 3 != 0:
                frame_idx += 1
                continue

            detections = run_inference(frame, model_name)
            # One violation per motorbike, grouping every bare-head rider on it.
            # A low floor drops only near-zero noise; real riders (even brief, blurry
            # ones) reach well above it, and dedup — not the threshold — controls the
            # count, so genuine violations are not filtered out.
            violations = find_violations(detections, min_confidence=0.3)

            # Track every violation by its expanded-head box in one shared namespace.
            anchors = [v.track_box() for v in violations]
            tracks = tracker.update(anchors)

            for viol, anchor in zip(violations, anchors):
                tid = _match_track(anchor, tracks)
                key = f"v-{tid}" if tid is not None else f"x-{frame_idx}-{len(processed)}"
                ref_box = anchor

                # Skip a group parked in place (a stopped bike).
                histories.setdefault(key, []).append(ref_box)
                if is_stationary(histories[key], threshold=5.0):
                    logger.info(f"Skipping stationary group {key}")
                    continue

                # One record per group, even across many sampled frames.
                if key in processed:
                    continue
                processed.add(key)

                # Evidence crop = the whole bike and every rider on it (biggest box).
                cx1, cy1, cx2, cy2 = viol.crop_box()
                ux1, uy1 = max(0, int(cx1)), max(0, int(cy1))
                ux2, uy2 = min(width, int(cx2)), min(height, int(cy2))
                crop_img = frame[uy1:uy2, ux1:ux2]
                if crop_img.size == 0:
                    continue

                # Upload crop to Supabase Storage
                crop_filename = f"crops/{user_id}/{video_id}_{key.replace('-', '_')}.jpg"
                try:
                    crop_url = upload_crop(crop_img, crop_filename)
                except Exception as exc:
                    logger.error(f"Failed to upload crop for {key}: {exc}")
                    continue

                # Insert violation record into Supabase DB
                try:
                    video_offset = float(frame_idx) / fps
                    track_int = abs(hash(key)) % 1_000_000
                    violation_id = insert_violation(
                        video_id=video_id,
                        user_id=user_id,
                        track_id=track_int,
                        model_name=model_name,
                        image_url=crop_url,
                        confidence=float(viol.confidence),
                        video_offset=video_offset,
                    )
                    logger.info(f"Inserted violation {violation_id} for {key}")

                    # Publish live violation notification to Redis pub-sub
                    if r_client:
                        r_client.publish("violation_detected", json.dumps({
                            "violationId": violation_id,
                            "videoId": video_id,
                            "timestamp": video_offset,
                            "confidence": float(viol.confidence),
                            "label": "non-helmet",
                        }))
                except Exception as exc:
                    logger.error(f"Failed to save violation: {exc}")

            frame_idx += 1

        cap.release()
        update_video_status(video_id, "done")

        # Publish completed status
        if r_client:
            from datetime import datetime, timezone
            try:
                r_client.publish(
                    "job_status_update",
                    json.dumps({
                        "jobId": video_id,
                        "fileName": filename,
                        "status": "done",
                        "modelUsed": model_name,
                        "completedAt": datetime.now(timezone.utc).isoformat()
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to publish done status: {e}")

        return {"status": "done", "video_id": video_id}

    except SoftTimeLimitExceeded:
        logger.warning("Soft time limit exceeded, clean termination of task")
        update_video_status(video_id, "failed")
        if r_client:
            try:
                r_client.publish(
                    "job_status_update",
                    json.dumps({
                        "jobId": video_id,
                        "fileName": filename,
                        "status": "failed",
                        "modelUsed": model_name,
                        "error": "Soft time limit exceeded"
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to publish failed status: {e}")
        return {"status": "failed", "error": "Soft time limit exceeded"}
    except Exception as exc:
        logger.error(f"Error processing video: {exc}")
        update_video_status(video_id, "failed")
        if r_client:
            try:
                r_client.publish(
                    "job_status_update",
                    json.dumps({
                        "jobId": video_id,
                        "fileName": filename,
                        "status": "failed",
                        "modelUsed": model_name,
                        "error": str(exc)
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to publish failed status: {e}")
        return {"status": "failed", "error": str(exc)}


def Detection_with_track(det, track_id):
    # Set track_id dynamically
    object.__setattr__(det, "track_id", track_id)
    return det
