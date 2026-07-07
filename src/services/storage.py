# src/services/storage.py
import logging
from typing import Optional
# Mock import for Supabase client
# from supabase import Client

logger = logging.getLogger(__name__)

def generate_signed_url(supabase_client, bucket_name: str, file_path: str, expiration_seconds: int = 3600) -> Optional[str]:
    """
    Generate a signed URL for a private file in a Supabase storage bucket (FR-021).
    
    Args:
        supabase_client: The initialized Supabase client
        bucket_name (str): The name of the storage bucket ('videos' or 'violations')
        file_path (str): The path to the file within the bucket
        expiration_seconds (int): How long the URL should be valid
        
    Returns:
        Optional[str]: The signed URL, or None if generation failed
    """
    try:
        response = supabase_client.storage.from_(bucket_name).create_signed_url(file_path, expiration_seconds)
        if response and 'signedURL' in response:
            return response['signedURL']
        return None
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {bucket_name}/{file_path}: {e}")
        return None

def upload_raw_video(supabase_client, user_id: str, video_id: str, filename: str, file_data: bytes) -> Optional[str]:
    """
    Upload a raw video file enforcing the user_id/video_id/filename path convention (FR-020).
    
    Returns:
        The exact file path in storage if successful, else None.
    """
    try:
        path = f"{user_id}/{video_id}/{filename}"
        supabase_client.storage.from_('videos').upload(path, file_data)
        return path
    except Exception as e:
        logger.error(f"Failed to upload raw video to videos/{user_id}/{video_id}/{filename}: {e}")
        return None

def upload_violation_crop(supabase_client, video_id: str, violation_id: str, cropname: str, file_data: bytes) -> Optional[str]:
    """
    Upload a violation crop image enforcing the video_id/violation_id/cropname path convention (FR-020).
    
    Returns:
        The exact file path in storage if successful, else None.
    """
    try:
        path = f"{video_id}/{violation_id}/{cropname}"
        supabase_client.storage.from_('violations').upload(path, file_data)
        return path
    except Exception as e:
        logger.error(f"Failed to upload violation crop to violations/{video_id}/{violation_id}/{cropname}: {e}")
        return None
