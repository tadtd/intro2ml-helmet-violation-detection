# src/workers/cleanup.py
import logging
from datetime import datetime, timedelta
# Mock import for Celery
# from celery import Celery
# from supabase import Client

logger = logging.getLogger(__name__)

# app = Celery('tasks', broker='redis://localhost:6379/0')

# @app.task
def cleanup_old_videos(supabase_client):
    """
    Celery beat periodic task to delete raw videos older than 3 days (FR-022).
    Explicitly excludes videos where status = 'processing'.
    
    Args:
        supabase_client: The initialized Supabase client
    """
    try:
        # Determine the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        # Query the database to find videos older than 3 days that are NOT processing
        response = supabase_client.table('videos') \
            .select('id, user_id, status') \
            .lt('created_at', cutoff_date.isoformat()) \
            .neq('status', 'processing') \
            .execute()
        
        if not response.data:
            logger.info("No expired videos found to delete.")
            return

        videos_to_delete = response.data
        bucket = supabase_client.storage.from_('videos')
        
        deleted_count = 0
        for video in videos_to_delete:
            # Reconstruct the file path: user_id/video_id/filename
            # Since filename isn't stored in the DB in this simplified schema,
            # we would list the files in the directory user_id/video_id/
            prefix = f"{video['user_id']}/{video['id']}/"
            files_response = bucket.list(prefix)
            
            if files_response:
                files_to_remove = [f"{prefix}{f['name']}" for f in files_response]
                if files_to_remove:
                    bucket.remove(files_to_remove)
                    deleted_count += len(files_to_remove)
                    
            # Update DB record if needed or rely on cascade/retention logic.
            # FR-022 says delete raw video files, but says "preserving database records permanently"
            # for violation crops, but wait, do we delete the video db record?
            # User Story 4: "deleting raw videos > 3 days old... keeping database logs permanently".
            # So we only delete from storage.
            
        logger.info(f"Successfully deleted {deleted_count} expired video files from storage.")
            
    except Exception as e:
        logger.error(f"Failed to execute cleanup task: {e}")
