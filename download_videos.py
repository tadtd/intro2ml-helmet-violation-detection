import re
import hashlib
from pathlib import Path

import pandas as pd
import yt_dlp

IN_CSV = Path("data/videos.csv")
VIDEOS_DIR = Path("data/videos")


def _safe_filename(text: str, max_len: int = 80) -> str:
    text = text.strip() or "video"
    text = re.sub(r"[\\/:*?\"<>|]", "_", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _url_suffix(url: str, length: int = 10) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return digest[:length]


def _download_one(url: str, outtmpl: str) -> str:
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def main() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {IN_CSV}")

    df = pd.read_csv(IN_CSV)
    if "video_url" not in df.columns:
        raise ValueError("Input CSV must contain column 'video_url'")

    if "download_status" not in df.columns:
        df["download_status"] = ""
    if "local_video_path" not in df.columns:
        df["local_video_path"] = ""

    for idx, row in df.iterrows():
        url = str(row.get("video_url", "")).strip()
        title = _safe_filename(str(row.get("title", "video")))
        if not url:
            df.at[idx, "download_status"] = "missing_url"
            continue

        unique_name = f"{title}_{_url_suffix(url)}"
        outtmpl = str(VIDEOS_DIR / f"{unique_name}.%(ext)s")

        prev_status = str(row.get("download_status", "")).strip().lower()
        prev_path = Path(str(row.get("local_video_path", "")).strip())
        if prev_status == "ok" and prev_path.exists():
            print(f"[SKIP] {url} -> {prev_path}")
            continue

        try:
            downloaded = _download_one(url, outtmpl)
            final_path = Path(downloaded)

            # yt-dlp can remux file extension; resolve final existing file.
            if not final_path.exists():
                candidates = list(VIDEOS_DIR.glob(f"{unique_name}.*"))
                if candidates:
                    final_path = candidates[0]

            df.at[idx, "download_status"] = "ok"
            df.at[idx, "local_video_path"] = str(final_path)
            print(f"[OK] {url} -> {final_path}")
        except Exception as exc:
            df.at[idx, "download_status"] = f"error: {exc}"
            print(f"[ERR] {url} -> {exc}")

    df.to_csv(IN_CSV, index=False, encoding="utf-8-sig")
    print(f"Updated CSV: {IN_CSV}")


if __name__ == "__main__":
    main()
