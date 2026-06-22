from .celery_app import celery_app


@celery_app.task(name="process_video")
def process_video(
    video_id: str,
    storage_path: str,
    filename: str,
    model_name: str,
    user_id: str,
) -> dict[str, str]:
    return {
        "video_id": video_id,
        "storage_path": storage_path,
        "filename": filename,
        "model_name": model_name,
        "user_id": user_id,
        "status": "not_implemented",
    }
