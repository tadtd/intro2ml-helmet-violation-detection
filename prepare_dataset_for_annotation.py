import random
import shutil
import hashlib
from pathlib import Path

import pandas as pd

RANDOM_SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IN_METADATA_CSV = Path("data/frames_metadata.csv")
OUT_DIR = Path("dataset")
TRAIN_DIR = OUT_DIR / "images" / "train"
VAL_DIR = OUT_DIR / "images" / "val"
TEST_DIR = OUT_DIR / "images" / "test"
OUT_METADATA_CSV = OUT_DIR / "images_metadata.csv"


def _pick_split(seed_key: str) -> str:
    # Stable split assignment by video key to avoid train/val/test leakage.
    digest = hashlib.sha1(seed_key.encode("utf-8")).hexdigest()[:8]
    x = int(digest, 16) / float(16**8)
    if x < TRAIN_RATIO:
        return "train"
    if x < TRAIN_RATIO + VAL_RATIO:
        return "val"
    return "test"


def _target_dir(split: str) -> Path:
    if split == "train":
        return TRAIN_DIR
    if split == "val":
        return VAL_DIR
    return TEST_DIR


def _reset_dataset_dirs() -> None:
    for d in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        if d.exists():
            for p in d.glob("*"):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    random.seed(RANDOM_SEED)

    if abs((TRAIN_RATIO + VAL_RATIO + TEST_RATIO) - 1.0) > 1e-9:
        raise ValueError("TRAIN_RATIO + VAL_RATIO + TEST_RATIO must equal 1.0")

    if not IN_METADATA_CSV.exists():
        raise FileNotFoundError(f"Missing metadata: {IN_METADATA_CSV}")

    _reset_dataset_dirs()

    df = pd.read_csv(IN_METADATA_CSV)
    required_cols = [
        "is_kept",
        "clean_frame_path",
        "stable_file_name",
        "stable_video_id",
        "width",
        "height",
        "source_video",
        "timestamp",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns in frames metadata: " + ", ".join(missing) + ". "
            "Please run filter_frames.py after updating it."
        )

    kept_df = df[df["is_kept"] == 1].copy()
    if kept_df.empty:
        raise ValueError("No kept images found. Run filter_frames.py first.")

    # Keep split assignment deterministic by sorting filename first.
    kept_df = kept_df.sort_values("stable_file_name").reset_index(drop=True)

    rows = []
    used_names = set()
    image_id = 1

    for _, row in kept_df.iterrows():
        src = Path(str(row["clean_frame_path"]))
        if not src.exists():
            continue

        split = _pick_split(str(row["stable_video_id"]))
        target_dir = _target_dir(split)

        file_name = str(row["stable_file_name"])
        if file_name in used_names:
            stem = Path(file_name).stem
            suffix = Path(file_name).suffix
            k = 1
            candidate = f"{stem}_{k:02d}{suffix}"
            while candidate in used_names:
                k += 1
                candidate = f"{stem}_{k:02d}{suffix}"
            file_name = candidate

        used_names.add(file_name)
        dst = target_dir / file_name
        shutil.copy2(src, dst)

        rows.append(
            {
                "image_id": image_id,
                "file_name": file_name,
                "width": int(row["width"]),
                "height": int(row["height"]),
                "source_video": str(row["source_video"]),
                "timestamp": float(row["timestamp"]),
                "split": split,
                "image_path": str(dst),
            }
        )
        image_id += 1

    out_df = pd.DataFrame(rows)
    out_df.to_csv(OUT_METADATA_CSV, index=False, encoding="utf-8-sig")

    counts = out_df["split"].value_counts().to_dict() if not out_df.empty else {}
    print(f"Done. Metadata saved to {OUT_METADATA_CSV}")
    print(
        "Train: {train}, Val: {val}, Test: {test}".format(
            train=counts.get("train", 0),
            val=counts.get("val", 0),
            test=counts.get("test", 0),
        )
    )


if __name__ == "__main__":
    main()
