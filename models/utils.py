import os
import random
from pathlib import Path

import numpy as np
import torch


def set_seed(seed: int = 42) -> None:
  random.seed(seed)
  np.random.seed(seed)
  torch.manual_seed(seed)
  if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)


def get_paths(dataset_slug: str = "helmet-violation-detection") -> tuple[Path, Path]:
  """Return (data_root, out_root), auto-detecting whether we are on Kaggle.

  Local:  data_root = ../data,  out_root = ./output
  Kaggle: data_root = /kaggle/input/<slug>/data,  out_root = /kaggle/working
  """
  on_kaggle = "KAGGLE_DATA_PROXY_PROJECT" in os.environ
  if on_kaggle:
    data_root = Path(f"/kaggle/input/{dataset_slug}/data")
    out_root = Path("/kaggle/working")
  else:
    data_root = Path(__file__).resolve().parent.parent / "data"
    out_root = Path(__file__).resolve().parent / "output"

  out_root.mkdir(parents=True, exist_ok=True)
  return data_root, out_root
