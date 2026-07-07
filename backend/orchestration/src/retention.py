import time
import logging
from datetime import datetime, timedelta, timezone

from common.config import get_settings
from common.db.client import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestration.retention")

settings = get_settings()


def run_retention_check():
    logger.info("Starting video retention daemon check")
    try:
        supabase = get_supabase_client()
        # Find videos created more than 3 days ago
        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        
        response = (
            supabase.table("videos")
            .select("id, storage_path")
            .lt("created_at", three_days_ago)
            .execute()
        )
        videos = response.data or []
        logger.info(f"Found {len(videos)} videos older than 3 days to prune")
        
        for video in videos:
            video_id = video["id"]
            storage_path = video["storage_path"]
            logger.info(f"Pruning video ID {video_id} (path: {storage_path})")
            
            # Delete from Supabase Storage
            try:
                supabase.storage.from_(settings.supabase_video_bucket).remove([storage_path])
                logger.info(f"Deleted storage object for video {video_id}")
            except Exception as e:
                logger.error(f"Failed to delete storage object {storage_path}: {e}")
                
            # Update video record to reflect raw file has been deleted
            try:
                # Set storage_path to empty or status to failed/done (or deleted)
                supabase.table("videos").update({"storage_path": "deleted"}).eq("id", video_id).execute()
                logger.info(f"Updated video database record for ID {video_id}")
            except Exception as e:
                logger.error(f"Failed to update database record for video {video_id}: {e}")
                
    except Exception as exc:
        logger.error(f"Error running retention check: {exc}")


if __name__ == "__main__":
    # Standard retention loop running every hour
    while True:
        run_retention_check()
        time.sleep(3600)  # Sleep for 1 hour
