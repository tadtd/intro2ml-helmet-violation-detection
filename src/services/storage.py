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
