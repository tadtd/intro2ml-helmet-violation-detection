from __future__ import annotations

from typing import TYPE_CHECKING

from common.config import get_settings
from common.db import DBError
from common.db.client import get_supabase_client

if TYPE_CHECKING:
    import numpy as np


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


def _signed_url_from_response(response: object) -> str | None:
    if isinstance(response, dict):
        return (
            response.get("signedURL")
            or response.get("signedUrl")
            or response.get("signed_url")
        )

    for attr in ("signed_url", "signedURL", "signedUrl"):
        value = getattr(response, attr, None)
        if value:
            return str(value)

    return None


def _storage_object_key(stored: str, bucket_name: str) -> str:
    """Return the object key inside a bucket from a key, bucket-prefixed path, or URL."""
    marker = f"/{bucket_name}/"
    if marker in stored:
        return stored.split(marker, 1)[1].split("?", 1)[0]

    prefix = f"{bucket_name}/"
    if stored.startswith(prefix):
        return stored[len(prefix):]

    return stored


def get_video_url(storage_path: str, expires_in: int = 3600) -> str:
    """Return a readable URL for an uploaded video.

    The video bucket is private, so a public URL would 400: sign it instead.
    """
    try:
        settings = get_settings()
        key = _storage_object_key(storage_path, settings.supabase_video_bucket)
        response = get_supabase_client().storage.from_(
            settings.supabase_video_bucket,
        ).create_signed_url(key, expires_in)
        signed_url = _signed_url_from_response(response)
        if not signed_url:
            raise DBError(f"Signed URL missing from response for {key}")
        return str(signed_url)
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to sign video URL") from exc


def upload_crop(img_array: np.ndarray, filename: str) -> str:
    """Encode an image crop as JPEG, upload it, and return its storage object path.

    The violations bucket is private, so we store the object path and hand out
    short-lived signed URLs at read time (see `sign_crop_url`). A public URL would
    404 with "Bucket not found".
    """
    try:
        import cv2

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
        return filename
    except DBError:
        raise
    except Exception as exc:
        raise DBError("Failed to upload crop") from exc


def _crop_object_key(stored: str) -> str:
    """The object key inside the violations bucket, from a path or a legacy URL.

    Older rows stored a full public URL; newer rows store the bare object path.
    """
    marker = f"/{get_settings().supabase_storage_bucket}/"
    if marker in stored:
        return stored.split(marker, 1)[1].split("?", 1)[0]
    return stored


def sign_crop_url(stored: str, expires_in: int = 3600) -> str | None:
    """Return a readable signed URL for a stored crop path (or legacy URL)."""
    if not stored:
        return None
    try:
        key = _storage_object_key(_crop_object_key(stored), get_settings().supabase_storage_bucket)
        response = get_supabase_client().storage.from_(
            get_settings().supabase_storage_bucket,
        ).create_signed_url(key, expires_in)
        return _signed_url_from_response(response)
    except Exception:
        return None


def delete_crop(filename: str) -> None:
    """Delete a crop image from Supabase Storage."""
    try:
        settings = get_settings()
        supabase = get_supabase_client()
        supabase.storage.from_(settings.supabase_storage_bucket).remove([filename])
    except Exception as exc:
        raise DBError("Failed to delete crop") from exc
