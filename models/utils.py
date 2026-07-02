import os
import random
import shutil
from pathlib import Path

import numpy as np
import torch

TRAIN_ANN_FILES = (
    "instances_train.json",
    "instances_train_merged.json",
    "instances_val.json",
    "instances_test.json",
)


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def is_kaggle() -> bool:
    return "KAGGLE_DATA_PROXY_PROJECT" in os.environ


def resolve_input_data_root() -> Path:
    """Return the dataset root (contains annotations/ and images/).

    Local:  ../data
    Kaggle: DATA_PATH env var (set in notebook before running scripts)
    """
    if is_kaggle():
        data_path = os.environ.get("DATA_PATH", "").strip()
        if not data_path:
            raise ValueError(
                "Set DATA_PATH in your notebook before running scripts:\n"
                '  DATA_PATH = "/kaggle/input/your-dataset"\n'
                '  os.environ["DATA_PATH"] = DATA_PATH'
            )
        base = Path(data_path)
    else:
        return Path(__file__).resolve().parent.parent / "data"

    if (base / "annotations").is_dir():
        return base
    if (base / "data" / "annotations").is_dir():
        return base / "data"
    return base


def _setup_kaggle_working_data(input_root: Path, out_root: Path) -> Path:
    """Build a writable data/ tree under /kaggle/working with symlinked images."""
    work_data = out_root / "data"
    work_data.mkdir(parents=True, exist_ok=True)

    work_images = work_data / "images"
    input_images = input_root / "images"
    if input_images.is_dir() and not work_images.exists():
        print(f"Copying images from {input_images} to {work_images} ...")
        shutil.copytree(input_images, work_images)

    src_ann = input_root / "annotations"
    dst_ann = work_data / "annotations"
    dst_ann.mkdir(parents=True, exist_ok=True)
    if src_ann.is_dir():
        for name in TRAIN_ANN_FILES:
            src = src_ann / name
            dst = dst_ann / name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)

    (work_data / "labels").mkdir(parents=True, exist_ok=True)
    return work_data


def get_paths() -> tuple[Path, Path]:
    """Return (data_root, out_root).

    Local:  data_root = ../data
    Kaggle: data_root = /kaggle/working/data (writable; images symlinked from DATA_PATH)
    """
    input_root = resolve_input_data_root()
    out_root = Path("/kaggle/working") if is_kaggle() else Path(__file__).resolve().parent / "output"
    out_root.mkdir(parents=True, exist_ok=True)

    if is_kaggle():
        data_root = _setup_kaggle_working_data(input_root, out_root)
    else:
        data_root = input_root

    return data_root, out_root


def get_train_ann_path(data_root: Path) -> Path:
    """Return train annotation file: merged if present, else original."""
    merged = data_root / "annotations" / "instances_train_merged.json"
    if merged.exists():
        return merged
    return data_root / "annotations" / "instances_train.json"
