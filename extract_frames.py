from pathlib import Path

import cv2
import pandas as pd

IN_CSV = Path("data/videos.csv")
FRAMES_RAW_DIR = Path("data/frames_raw")
OUT_METADATA_CSV = Path("data/frames_metadata.csv")

FRAME_EVERY_SEC = 1.0
MAX_FRAMES_PER_VIDEO = 1000


def _laplacian_var(gray_img) -> float:
    return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())


def main() -> None:
    FRAMES_RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {IN_CSV}")

    videos_df = pd.read_csv(IN_CSV)
    if "local_video_path" not in videos_df.columns:
        raise ValueError("Please run download_videos.py first (missing 'local_video_path').")

    rows = []

    for _, video_row in videos_df.iterrows():
        video_path = Path(str(video_row.get("local_video_path", "")).strip())
        if not video_path.exists():
            continue

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_interval = max(1, int(fps * FRAME_EVERY_SEC)) if fps > 0 else 25

        video_stem = video_path.stem
        out_dir = FRAMES_RAW_DIR / video_stem
        out_dir.mkdir(parents=True, exist_ok=True)

        frame_idx = 0
        saved = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval != 0:
                frame_idx += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur_score = _laplacian_var(gray)

            frame_name = f"frame_{saved:06d}.jpg"
            frame_path = out_dir / frame_name
            cv2.imwrite(str(frame_path), frame)

            h, w = frame.shape[:2]
            timestamp_sec = frame_idx / fps if fps > 0 else 0.0

            rows.append(
                {
                    "video_url": video_row.get("video_url", ""),
                    "query": video_row.get("query", ""),
                    "title": video_row.get("title", ""),
                    "video_path": str(video_path),
                    "frame_path": str(frame_path),
                    "frame_index": int(frame_idx),
                    "timestamp_sec": float(timestamp_sec),
                    "width": int(w),
                    "height": int(h),
                    "blur_score": float(blur_score),
                }
            )

            saved += 1
            frame_idx += 1

            if saved >= MAX_FRAMES_PER_VIDEO:
                break

        cap.release()
        print(f"[OK] {video_path.name}: saved {saved} frames")

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_METADATA_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved metadata to {OUT_METADATA_CSV} ({len(out_df)} rows)")


if __name__ == "__main__":
    main()
