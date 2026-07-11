from typing import NotRequired, TypedDict

from common.db.constants import ModelName, VideoStatus


class VideoInsert(TypedDict):
    user_id: str
    filename: str
    model_used: ModelName
    storage_path: str
    content_type: NotRequired[str | None]


class ViolationInsert(TypedDict):
    video_id: str | None
    user_id: str
    track_id: int
    model_used: ModelName
    image_url: str
    confidence: float
    video_offset: float


class VideoStatusUpdate(TypedDict):
    status: VideoStatus