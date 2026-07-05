import logging
from common.db.videos import get_video, update_video_status
from common.celery import celery_app

logger = logging.getLogger("orchestration.lifecycle")


def get_job_status(video_id: str) -> dict[str, str]:
    try:
        video = get_video(video_id)
        return {
            "video_id": video_id,
            "status": video.get("status", "unknown"),
            "model_used": video.get("model_used", ""),
            "filename": video.get("filename", "")
        }
    except Exception as exc:
        logger.error(f"Error fetching status for {video_id}: {exc}")
        return {"video_id": video_id, "status": "not_found", "error": str(exc)}
