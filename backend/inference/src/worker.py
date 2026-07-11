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

from .heuristics.crop import get_composite_union_box
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

        tracker = IoUTracker(iou_threshold=0.3)
        processed_tracks = set()
        track_histories = {}  # track_id -> list of box coordinates

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every 5th frame to run faster in local CPU docker
            if frame_idx % 5 != 0:
                frame_idx += 1
                continue

            # Run ONNX or stub inference
            detections = run_inference(frame, model_name)
            
            # Map detections to tracker boxes
            boxes = [det.box for det in detections]
            tracks = tracker.update(boxes)

            # Record box history for each active track
            for track in tracks:
                if track.track_id not in track_histories:
                    track_histories[track.track_id] = []
                track_histories[track.track_id].append(track.box)

            # Associate tracker IDs with detections
            for det in detections:
                for track in tracks:
                    # check if the boxes match exactly or have high IoU
                    from .tracker import iou
                    if iou(det.box, track.box) > 0.9:
                        det = Detection_with_track(det, track.track_id)
                        break

            # Find motorbike + non-helmet associations
            violations = find_violations(detections)

            for viol in violations:
                non_helmet = viol.non_helmet
                # Assign a pseudo track ID if it's matched with motorbike track ID
                track_id = getattr(viol.motorbike, "track_id", None) or 999
                
                # Apply stationary vehicle filtering heuristic
                if track_id in track_histories:
                    if is_stationary(track_histories[track_id], threshold=5.0):
                        logger.info(f"Skipping stationary track {track_id}")
                        continue

                # Check if we have already reported this violation for this track
                if track_id in processed_tracks:
                    continue
                processed_tracks.add(track_id)

                # Compute composite union crop box coordinates
                ux1, uy1, ux2, uy2 = get_composite_union_box(
                    viol.motorbike.box,
                    non_helmet.box,
                    width,
                    height
                )

                # Crop image
                crop_img = frame[uy1:uy2, ux1:ux2]
                if crop_img.size == 0:
                    continue

                # Upload crop to Supabase Storage
                crop_filename = f"crops/{user_id}/{video_id}_{track_id}.jpg"
                try:
                    crop_url = upload_crop(crop_img, crop_filename)
                except Exception as exc:
                    logger.error(f"Failed to upload crop for track {track_id}: {exc}")
                    continue

                # Insert violation record into Supabase DB
                try:
                    violation_id = insert_violation(
                        video_id=video_id,
                        user_id=user_id,
                        track_id=track_id,
                        model_name=model_name,
                        image_url=crop_url,
                        confidence=float(non_helmet.confidence),
                    )
                    logger.info(f"Inserted violation {violation_id} for track {track_id}")

                    # Publish live violation notification to Redis pub-sub
                    if r_client:
                        event_payload = {
                            "violationId": violation_id,
                            "videoId": video_id,
                            "timestamp": float(frame_idx) / fps,
                            "confidence": float(non_helmet.confidence),
                            "label": "non-helmet"
                        }
                        r_client.publish("violation_detected", json.dumps(event_payload))
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
