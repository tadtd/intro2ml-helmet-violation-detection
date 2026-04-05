import shutil
import hashlib
from collections import defaultdict
from pathlib import Path

import cv2
import pandas as pd

IN_METADATA_CSV = Path("data/frames_metadata.csv")
FRAMES_CLEAN_DIR = Path("data/frames_clean")

MIN_BLUR_SCORE = 80.0
MIN_BRIGHTNESS = 40.0
MAX_BRIGHTNESS = 220.0
SIMILARITY_THRESHOLD = 2.0
TOP_SCORE_KEEP_RATIO = 0.45
MIN_KEEP_PER_VIDEO = 25
MAX_KEEP_PER_VIDEO = 250


def _reset_output_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return

    for p in path.rglob("*"):
        if p.is_file():
            p.unlink()

    for p in sorted(path.rglob("*"), reverse=True):
        if p.is_dir():
            try:
                p.rmdir()
            except OSError:
                pass


def _stable_video_id(video_key: str) -> str:
    digest = hashlib.sha1(video_key.encode("utf-8")).hexdigest()[:8]
    return f"video{digest}"


def _brightness(gray_img) -> float:
    return float(gray_img.mean())


def _tiny_signature(gray_img):
    tiny = cv2.resize(gray_img, (16, 16), interpolation=cv2.INTER_AREA)
    return tiny.astype("float32")


def _distance(sig_a, sig_b) -> float:
    return float(abs(sig_a - sig_b).mean())


def _to_ms(timestamp_sec: float) -> int:
    return max(0, int(round(float(timestamp_sec) * 1000.0)))


def _skin_ratio(bgr_img) -> float:
    ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)

    # Conservative skin color mask from two color spaces.
    mask_ycrcb = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
    mask_hsv = cv2.inRange(hsv, (0, 20, 70), (25, 255, 255))
    skin_mask = cv2.bitwise_and(mask_ycrcb, mask_hsv)

    return float((skin_mask > 0).mean())


def _no_helmet_score(bgr_img) -> float:
    h, w = bgr_img.shape[:2]
    y1, y2 = int(h * 0.06), int(h * 0.55)
    x1, x2 = int(w * 0.2), int(w * 0.8)
    roi = bgr_img[y1:y2, x1:x2]

    if roi.size == 0:
        return 0.0

    skin = _skin_ratio(roi)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    sat_mean = float(hsv[:, :, 1].mean()) / 255.0
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    texture = min(1.0, float(cv2.Laplacian(gray, cv2.CV_64F).var()) / 900.0)

    score = 0.7 * skin + 0.2 * (1.0 - sat_mean) + 0.1 * texture
    return float(max(0.0, min(1.0, score)))


def main() -> None:
    _reset_output_dir(FRAMES_CLEAN_DIR)

    if not IN_METADATA_CSV.exists():
        raise FileNotFoundError(f"Missing input metadata: {IN_METADATA_CSV}")

    df = pd.read_csv(IN_METADATA_CSV)
    if "frame_path" not in df.columns:
        raise ValueError("Metadata CSV must contain column 'frame_path'.")

    if "is_kept" not in df.columns:
        df["is_kept"] = 0
    if "clean_frame_path" not in df.columns:
        df["clean_frame_path"] = ""
    if "filter_reason" not in df.columns:
        df["filter_reason"] = ""
    if "no_helmet_score" not in df.columns:
        df["no_helmet_score"] = 0.0
    if "stable_video_id" not in df.columns:
        df["stable_video_id"] = ""
    if "stable_file_name" not in df.columns:
        df["stable_file_name"] = ""
    if "source_video" not in df.columns:
        df["source_video"] = ""
    if "timestamp" not in df.columns:
        df["timestamp"] = 0.0
    if "image_id" not in df.columns:
        df["image_id"] = 0

    # Reset output columns for deterministic reruns.
    df["is_kept"] = 0
    df["clean_frame_path"] = ""
    df["filter_reason"] = ""
    df["no_helmet_score"] = 0.0
    df["stable_video_id"] = ""
    df["stable_file_name"] = ""
    df["source_video"] = ""
    df["timestamp"] = 0.0
    df["image_id"] = 0

    candidate_indices = defaultdict(list)
    last_sig_per_video = {}

    for idx, row in df.iterrows():
        frame_path = Path(str(row.get("frame_path", "")).strip())
        video_path = str(row.get("video_path", "")).strip()

        if not frame_path.exists():
            df.at[idx, "filter_reason"] = "missing_frame"
            continue

        img = cv2.imread(str(frame_path))
        if img is None:
            df.at[idx, "filter_reason"] = "read_failed"
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = float(row.get("blur_score", 0.0))
        bright = _brightness(gray)

        if blur_score < MIN_BLUR_SCORE:
            df.at[idx, "filter_reason"] = "blurry"
            continue

        if bright < MIN_BRIGHTNESS:
            df.at[idx, "filter_reason"] = "too_dark"
            continue

        if bright > MAX_BRIGHTNESS:
            df.at[idx, "filter_reason"] = "too_bright"
            continue

        sig = _tiny_signature(gray)
        prev_sig = last_sig_per_video.get(video_path)
        if prev_sig is not None and _distance(sig, prev_sig) < SIMILARITY_THRESHOLD:
            df.at[idx, "filter_reason"] = "near_duplicate"
            continue

        score = _no_helmet_score(img)
        df.at[idx, "no_helmet_score"] = score
        df.at[idx, "filter_reason"] = "candidate"
        candidate_indices[video_path].append(idx)
        last_sig_per_video[video_path] = sig

    kept_count = 0
    next_image_id = 1
    used_names = set()
    for video_path, idx_list in candidate_indices.items():
        first_idx = idx_list[0]
        video_url = str(df.at[first_idx, "video_url"]).strip() if "video_url" in df.columns else ""
        key = video_url or video_path or "unknown"
        stable_video_id = _stable_video_id(key)
        source_video = Path(video_path).name if video_path else "unknown.mp4"
        ranked = sorted(idx_list, key=lambda i: float(df.at[i, "no_helmet_score"]), reverse=True)
        target_keep = int(len(ranked) * TOP_SCORE_KEEP_RATIO)
        target_keep = max(MIN_KEEP_PER_VIDEO, target_keep)
        target_keep = min(MAX_KEEP_PER_VIDEO, target_keep)
        target_keep = min(target_keep, len(ranked))

        for rank, idx in enumerate(ranked):
            frame_path = Path(str(df.at[idx, "frame_path"]))

            if rank >= target_keep:
                df.at[idx, "filter_reason"] = "low_no_helmet_score"
                continue

            timestamp_sec = float(df.at[idx, "timestamp_sec"]) if "timestamp_sec" in df.columns else 0.0
            ts_ms = _to_ms(timestamp_sec)
            base_name = f"{stable_video_id}_t{ts_ms:06d}.jpg"
            stable_name = base_name
            collision_idx = 1
            while stable_name in used_names:
                stable_name = base_name.replace(".jpg", f"_{collision_idx:02d}.jpg")
                collision_idx += 1
            used_names.add(stable_name)

            clean_path = FRAMES_CLEAN_DIR / stable_name
            clean_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(frame_path, clean_path)

            df.at[idx, "is_kept"] = 1
            df.at[idx, "clean_frame_path"] = str(clean_path)
            df.at[idx, "filter_reason"] = "kept_priority_no_helmet"
            df.at[idx, "stable_video_id"] = stable_video_id
            df.at[idx, "stable_file_name"] = stable_name
            df.at[idx, "source_video"] = source_video
            df.at[idx, "timestamp"] = timestamp_sec
            df.at[idx, "image_id"] = next_image_id
            kept_count += 1
            next_image_id += 1

    df.to_csv(IN_METADATA_CSV, index=False, encoding="utf-8-sig")
    print(f"Filtered frames: kept {kept_count}/{len(df)}")
    print(f"Updated metadata: {IN_METADATA_CSV}")


if __name__ == "__main__":
    main()
