"""
Helmet Crawler – YouTube → Frames → Ollama LLaVA → no-helmet images.

Functions
---------
search_and_download()   Download YouTube videos matching search queries.
extract_frames()        Pull frames from a video at a fixed interval, dedup with dhash.
detect_no_helmet()      Two-stage Ollama LLaVA analysis on a single frame.
run_pipeline()          End-to-end: download → extract → detect → save results.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess
from pathlib import Path

import cv2
import imagehash
import ollama
import pandas as pd
from PIL import Image
from tqdm import tqdm

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. YouTube search & download
# ---------------------------------------------------------------------------

def search_and_download(
    queries: list[str] | None = None,
    max_per_query: int = config.MAX_VIDEOS_PER_QUERY,
    max_total: int = config.MAX_VIDEOS_TOTAL,
    max_duration: int = config.MAX_VIDEO_DURATION,
    resolution: str = config.VIDEO_RESOLUTION,
    download_dir: str = config.DOWNLOAD_DIR,
) -> list[dict]:
    """Search YouTube and download matching videos with yt-dlp.

    Returns a list of dicts: {"video_id", "title", "url", "path"}.
    """
    queries = queries or config.SEARCH_QUERIES
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    height_map = {"360p": 360, "480p": 480, "720p": 720, "1080p": 1080}
    max_height = height_map.get(resolution, 480)

    downloaded: list[dict] = []
    seen_ids: set[str] = set()

    for query in queries:
        if len(downloaded) >= max_total:
            break

        log.info("Searching YouTube: %s", query)
        search_cmd = [
            "yt-dlp",
            f"ytsearch{max_per_query}:{query}",
            "--dump-json",
            "--flat-playlist",
            "--no-download",
        ]
        result = subprocess.run(
            search_cmd, capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log.warning("yt-dlp search failed for query '%s': %s", query, result.stderr[:300])
            continue

        for line in result.stdout.strip().splitlines():
            if len(downloaded) >= max_total:
                break
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue

            vid = info.get("id", info.get("url", ""))
            duration = info.get("duration") or 0
            if vid in seen_ids:
                continue
            if duration and duration > max_duration:
                log.info("Skipping %s (duration %ss > %ss)", vid, duration, max_duration)
                continue

            seen_ids.add(vid)
            url = f"https://www.youtube.com/watch?v={vid}"
            out_template = str(download_dir / f"%(id)s.%(ext)s")

            dl_cmd = [
                "yt-dlp",
                url,
                "-f", f"bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]",
                "--merge-output-format", "mp4",
                "-o", out_template,
                "--no-playlist",
                "--socket-timeout", "30",
            ]
            log.info("Downloading %s ...", vid)
            dl = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=600)
            if dl.returncode != 0:
                log.warning("Download failed for %s: %s", vid, dl.stderr[:300])
                continue

            video_path = download_dir / f"{vid}.mp4"
            if not video_path.exists():
                candidates = list(download_dir.glob(f"{vid}.*"))
                video_path = candidates[0] if candidates else video_path

            if video_path.exists():
                downloaded.append({
                    "video_id": vid,
                    "title": info.get("title", ""),
                    "url": url,
                    "path": str(video_path),
                })
                log.info("Saved → %s", video_path)

    log.info("Downloaded %d videos total.", len(downloaded))
    return downloaded


# ---------------------------------------------------------------------------
# 2. Frame extraction with dedup
# ---------------------------------------------------------------------------

def _dhash(image: Image.Image, hash_size: int = 8) -> imagehash.ImageHash:
    return imagehash.dhash(image, hash_size=hash_size)


def extract_frames(
    video_path: str,
    interval: float = config.FRAME_INTERVAL,
    dup_threshold: int = config.DUPLICATE_THRESHOLD,
) -> list[dict]:
    """Extract frames from *video_path* every *interval* seconds.

    Returns list of dicts: {"timestamp_s", "image"(PIL), "path"(video)}.
    Skips near-duplicate frames (dhash hamming distance < dup_threshold).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log.error("Cannot open video: %s", video_path)
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frame_step = int(fps * interval)

    frames: list[dict] = []
    prev_hash = None
    frame_idx = 0

    log.info(
        "Extracting frames from %s (%.1fs, %.1f fps, step=%d)",
        Path(video_path).name, duration, fps, frame_step,
    )

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, bgr = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        h = _dhash(pil_img)

        if prev_hash is not None and (h - prev_hash) < dup_threshold:
            frame_idx += frame_step
            continue

        prev_hash = h
        timestamp_s = round(frame_idx / fps, 2)
        frames.append({
            "timestamp_s": timestamp_s,
            "image": pil_img,
            "path": video_path,
        })
        frame_idx += frame_step

    cap.release()
    log.info("Extracted %d unique frames from %s", len(frames), Path(video_path).name)
    return frames


# ---------------------------------------------------------------------------
# 3. No-helmet detection (two-stage Ollama LLaVA)
# ---------------------------------------------------------------------------

def _image_to_bytes(img: Image.Image, max_side: int = 1024) -> bytes:
    """Resize if needed and return JPEG bytes."""
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _ollama_client() -> ollama.Client:
    """Client for the running Ollama server (GPU is chosen by the server, not this SDK)."""
    return ollama.Client(host=config.OLLAMA_HOST)


def _ask_ollama(image_bytes: bytes, prompt: str, model: str = config.OLLAMA_MODEL) -> str:
    """Send an image + prompt to Ollama and return the text response."""
    b64 = base64.b64encode(image_bytes).decode()
    client = _ollama_client()
    response = client.chat(
        model=model,
        messages=[{
            "role": "user",
            "content": prompt,
            "images": [b64],
        }],
    )
    return response["message"]["content"].strip()


def _parse_stage2(text: str) -> dict | None:
    """Try to extract JSON from the LLM response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        if "violations" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None


def detect_no_helmet(
    img: Image.Image,
    two_stage: bool = config.TWO_STAGE_DETECTION,
    confidence_filter: list[str] = config.CONFIDENCE_FILTER,
    retry: bool = config.RETRY_ON_PARSE_FAIL,
    model: str = config.OLLAMA_MODEL,
) -> dict | None:
    """Analyse a single frame for no-helmet violations.

    Returns a dict with ``violations`` list and ``count``, or *None* if
    no violation is detected.
    """
    image_bytes = _image_to_bytes(img)

    # Stage 1 – quick yes/no pre-filter
    if two_stage:
        answer = _ask_ollama(image_bytes, config.STAGE1_PROMPT, model)
        if "YES" not in answer.upper():
            return None

    # Stage 2 – detailed JSON analysis
    raw = _ask_ollama(image_bytes, config.STAGE2_PROMPT, model)
    result = _parse_stage2(raw)

    if result is None and retry:
        raw = _ask_ollama(image_bytes, config.STAGE2_RETRY_PROMPT, model)
        result = _parse_stage2(raw)

    if result is None:
        return None

    # Filter by confidence
    if confidence_filter:
        result["violations"] = [
            v for v in result.get("violations", [])
            if v.get("confidence", "").lower() in confidence_filter
        ]
        result["count"] = len(result["violations"])

    if result["count"] == 0:
        return None

    result["_raw"] = raw
    return result


# ---------------------------------------------------------------------------
# 4. End-to-end pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    queries: list[str] | None = None,
    skip_download: bool = False,
    video_paths: list[str] | None = None,
    *,
    max_per_query: int | None = None,
    max_total: int | None = None,
    max_duration: int | None = None,
    resolution: str | None = None,
    download_dir: str | None = None,
    frame_interval: float | None = None,
    dup_threshold: int | None = None,
    output_dir: str | None = None,
    results_csv: str | None = None,
    ollama_model: str | None = None,
) -> pd.DataFrame:
    """Run the full crawl → extract → detect pipeline.

    Parameters
    ----------
    queries : optional override for search queries (replaces defaults when non-empty)
    skip_download : if True, skip YouTube download and use *video_paths*
    video_paths : list of local video files (used when skip_download=True)
    max_per_query, max_total, max_duration, resolution, download_dir
        Passed to ``search_and_download`` when not None.
    frame_interval, dup_threshold
        Passed to ``extract_frames`` when not None.
    output_dir, results_csv
        Override output locations when not None.
    ollama_model
        Vision model name for ``detect_no_helmet`` when not None.

    Returns a DataFrame with all detected violations.
    """
    out_dir = output_dir if output_dir is not None else config.OUTPUT_DIR
    csv_path = results_csv if results_csv is not None else config.RESULTS_CSV
    interval = frame_interval if frame_interval is not None else config.FRAME_INTERVAL
    dup_t = dup_threshold if dup_threshold is not None else config.DUPLICATE_THRESHOLD
    model = ollama_model if ollama_model is not None else config.OLLAMA_MODEL

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    # --- Download ---
    if skip_download:
        videos = [
            {"video_id": Path(p).stem, "url": "", "title": "", "path": p}
            for p in (video_paths or [])
        ]
    else:
        sd_kwargs: dict = {"queries": queries}
        if max_per_query is not None:
            sd_kwargs["max_per_query"] = max_per_query
        if max_total is not None:
            sd_kwargs["max_total"] = max_total
        if max_duration is not None:
            sd_kwargs["max_duration"] = max_duration
        if resolution is not None:
            sd_kwargs["resolution"] = resolution
        if download_dir is not None:
            sd_kwargs["download_dir"] = download_dir
        videos = search_and_download(**sd_kwargs)

    if not videos:
        log.warning("No videos to process.")
        return pd.DataFrame()

    rows: list[dict] = []
    total_frames = 0
    total_violations = 0

    for vid_info in videos:
        vid_id = vid_info["video_id"]
        vid_url = vid_info["url"]
        vid_path = vid_info["path"]
        log.info("Processing video: %s (%s)", vid_id, vid_info.get("title", ""))

        frames = extract_frames(vid_path, interval=interval, dup_threshold=dup_t)
        total_frames += len(frames)

        for frame in tqdm(frames, desc=f"Detecting [{vid_id}]", unit="frame"):
            result = detect_no_helmet(frame["image"], model=model)
            if result is None:
                continue

            ts = frame["timestamp_s"]
            fname = f"{vid_id}_{ts}s.jpg"
            out_path = os.path.join(out_dir, fname)
            frame["image"].save(out_path, quality=90)

            total_violations += 1
            rows.append({
                "video_id": vid_id,
                "video_url": vid_url,
                "timestamp_s": ts,
                "frame_path": out_path,
                "violation_count": result["count"],
                "violations_json": json.dumps(result["violations"]),
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(csv_path, index=False)
        log.info("Results saved to %s", csv_path)

    # --- Summary ---
    log.info("=" * 50)
    log.info("SUMMARY")
    log.info("  Videos processed : %d", len(videos))
    log.info("  Frames analysed  : %d", total_frames)
    log.info("  Violations found : %d", total_violations)
    if total_frames:
        log.info("  Violation rate   : %.1f%%", 100 * total_violations / total_frames)
    log.info("  Output directory : %s", out_dir)
    log.info("=" * 50)

    return df
