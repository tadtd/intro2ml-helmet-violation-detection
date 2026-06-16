from .celery_app import celery_app


@celery_app.task(name="process_video")
def process_video(filename: str, model_name: str, user_id: str) -> dict[str, str]:
    return {
        "filename": filename,
        "model_name": model_name,
        "user_id": user_id,
        "status": "not_implemented",
    }
