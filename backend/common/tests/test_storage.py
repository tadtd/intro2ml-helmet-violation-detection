from types import SimpleNamespace

from common.db.storage import _signed_url_from_response, _storage_object_key


def test_storage_object_key_accepts_bucket_prefixed_paths():
    assert _storage_object_key("videos/user/video.mp4", "videos") == "user/video.mp4"


def test_storage_object_key_accepts_supabase_storage_urls():
    stored = "https://example.supabase.co/storage/v1/object/sign/videos/user/video.mp4?token=abc"

    assert _storage_object_key(stored, "videos") == "user/video.mp4"


def test_signed_url_from_response_accepts_dict_and_object_shapes():
    assert _signed_url_from_response({"signed_url": "https://signed.example/video.mp4"}) == "https://signed.example/video.mp4"
    assert _signed_url_from_response(SimpleNamespace(signed_url="https://signed.example/video.mp4")) == "https://signed.example/video.mp4"
