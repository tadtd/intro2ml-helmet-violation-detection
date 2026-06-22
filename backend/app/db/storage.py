import cv2
import numpy as np

from app.config import get_settings
from app.db import DBError
from app.db.client import get_supabase_client


def upload_bytes(
    bucket_name: str,
    object_path: str,
    content: bytes,
    content_type: str,
) -> str:
    """Upload bytes to Supabase Storage and return the object path."""
    try:
        supabase = get_supabase_client()
        supabase.storage.from_(bucket_name).upload(
            object_path,
            content,
            file_options={
                "content-type": content_type,
                "upsert": "true",
            },
        )
        return object_path
    except Exception as exc:
        raise DBError("Failed to upload storage object") from exc


def upload_video(content: bytes, filename: str, content_type: str | None) -> str:
    """Upload an original video file and return its storage object path."""
    settings = get_settings()
    safe_content_type = content_type or "application/octet-stream"
    return upload_bytes(
        bucket_name=settings.supabase_video_bucket,
        object_path=filename,
        content=content,
        content_type=safe_content_type,
    )


def upload_crop(img_array: np.ndarray, filename: str) -> str:
    """Encode an image crop as JPEG, upload it, and return its public URL."""
    try:
        settings = get_settings()
        supabase = get_supabase_client()
        success, encoded_image = cv2.imencode(".jpg", img_array)
        if not success:
            raise DBError("Failed to encode crop as JPEG")

        supabase.storage.from_(settings.supabase_storage_bucket).upload(
            filename,
            encoded_image.tobytes(),
            file_options={
                "content-type": "image/jpeg",
                "upsert": "true",
            },
        )
        public_url = supabase.storage.from_(
            settings.supabase_storage_bucket,
        ).get_public_url(filename)
        return str(public_url)
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to upload crop") from exc


def delete_crop(filename: str) -> None:
    """Delete a crop image from Supabase Storage."""
    try:
        settings = get_settings()
        supabase = get_supabase_client()
        supabase.storage.from_(settings.supabase_storage_bucket).remove([filename])
    except Exception as exc:
        raise DBError("Failed to delete crop") from exc
