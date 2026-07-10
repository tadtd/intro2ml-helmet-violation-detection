from inference.src import stream


def test_named_source_resolves_to_demo_file():
    resolved = stream._resolve_source("demo-violation")
    assert resolved.endswith("violation_demo.mp4")


def test_verbatim_url_is_passed_through():
    url = "rtsp://192.168.1.10:554/stream"
    assert stream._resolve_source(url) == url


def test_empty_source_falls_back_to_default():
    assert stream._resolve_source(None) == stream.DEFAULT_SOURCE


def test_local_file_is_loopable_but_url_is_not():
    assert stream._is_loopable_file(stream.DEFAULT_SOURCE) is True
    assert stream._is_loopable_file("rtsp://cam/stream") is False
    assert stream._is_loopable_file("https://host/live.m3u8") is False


def test_youtube_urls_are_recognised():
    assert stream._is_youtube("https://www.youtube.com/watch?v=abc123") is True
    assert stream._is_youtube("https://youtu.be/abc123") is True
    assert stream._is_youtube("rtsp://cam/stream") is False
    assert stream._is_youtube("https://host/live.m3u8") is False


def test_model_name_normalisation():
    # Both the id and the stored display name resolve to the model id.
    assert stream._normalize_model("yolo") == "yolo"
    assert stream._normalize_model("YOLO") == "yolo"
    assert stream._normalize_model("RT-DETR") == "rtdetr"
    assert stream._normalize_model("Faster R-CNN") == "fasterrcnn"
    # Unknown or missing falls back to the default.
    assert stream._normalize_model(None) == stream.DEFAULT_MODEL
    assert stream._normalize_model("bogus") == stream.DEFAULT_MODEL
