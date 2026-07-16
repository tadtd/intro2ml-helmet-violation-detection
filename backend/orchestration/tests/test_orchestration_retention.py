import logging

try:
    from orchestration.src.retention import run_retention_check
except ModuleNotFoundError:
    from src.retention import run_retention_check


def test_run_retention_check_keeps_uploaded_videos(caplog):
    caplog.set_level(logging.INFO)

    run_retention_check()

    assert "retention pruning is disabled" in caplog.text
