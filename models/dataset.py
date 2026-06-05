from pathlib import Path
from typing import Callable, Optional
import random
import shutil

import torch
import torchvision.transforms.functional as TF
import yaml
from PIL import Image
from pycocotools.coco import COCO
from torch.utils.data import Dataset


class CocoDetectionDataset(Dataset):
    """COCO-format detection dataset for use with Faster R-CNN.

    Returns (image_tensor, target_dict) where target_dict has keys:
        boxes     — FloatTensor[N, 4] in xyxy pixel coordinates
        labels    — Int64Tensor[N]
        image_id  — Int64Tensor[1]
        area      — FloatTensor[N]
        iscrowd   — Int64Tensor[N]
    """

    def __init__(
        self,
        ann_json: Path,
        img_dir: Path,
        transforms: Optional[Callable] = None,
    ) -> None:
        self.coco = COCO(str(ann_json))
        self.img_dir = Path(img_dir)
        self.transforms = transforms
        self.ids = list(self.coco.imgs.keys())

    def __len__(self) -> int:
        return len(self.ids)

    def __getitem__(self, idx: int):
        img_id = self.ids[idx]
        img_info = self.coco.loadImgs(img_id)[0]
        img = Image.open(self.img_dir / img_info["file_name"]).convert("RGB")
        img_tensor = TF.to_tensor(img)

        ann_ids = self.coco.getAnnIds(imgIds=img_id)
        anns = self.coco.loadAnns(ann_ids)

        boxes, labels, areas, iscrowd = [], [], [], []
        for ann in anns:
            x, y, w, h = ann["bbox"]
            boxes.append([x, y, x + w, y + h])  # xywh → xyxy
            labels.append(ann["category_id"])
            areas.append(ann["area"])
            iscrowd.append(int(ann.get("iscrowd", 0)))

        target = {
            "boxes": torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.tensor(labels, dtype=torch.int64),
            "image_id": torch.tensor([img_id], dtype=torch.int64),
            "area": torch.tensor(areas, dtype=torch.float32),
            "iscrowd": torch.tensor(iscrowd, dtype=torch.int64),
        }

        if self.transforms is not None:
            img_tensor, target = self.transforms(img_tensor, target)

        return img_tensor, target

    @staticmethod
    def collate_fn(batch):
        return tuple(zip(*batch))


def coco_to_yolo_labels(
    ann_json: Path,
    data_root: Path,
    split: str,
    *,
    force: bool = False,
) -> Path:
    """Convert COCO annotations to YOLO .txt label files.

    Writes one .txt per image to data_root/labels/{split}/.
    Each line: <class_id> <cx> <cy> <w> <h>  (normalised 0-1, class_id 0-indexed).
    Idempotent — skips if the label directory already contains .txt files,
    unless force=True.

    Returns the label directory path.
    """
    out_dir = Path(data_root) / "labels" / split
    out_dir.mkdir(parents=True, exist_ok=True)

    if not force and list(out_dir.glob("*.txt")):
        return out_dir

    if force:
        for txt in out_dir.glob("*.txt"):
            txt.unlink()

    coco = COCO(str(ann_json))
    for img_id, img_info in coco.imgs.items():
        w_img = img_info["width"]
        h_img = img_info["height"]

        ann_ids = coco.getAnnIds(imgIds=img_id)
        anns = coco.loadAnns(ann_ids)

        lines = []
        for ann in anns:
            x, y, w, h = ann["bbox"]
            cx = (x + w / 2) / w_img
            cy = (y + h / 2) / h_img
            nw = w / w_img
            nh = h / h_img
            cls_id = ann["category_id"] - 1  # COCO 1-indexed → YOLO 0-indexed
            lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

        stem = Path(img_info["file_name"]).stem
        (out_dir / f"{stem}.txt").write_text("\n".join(lines))

    return out_dir


def resolve_image_path(data_root: Path, file_name: str) -> Path:
    """Locate an image under data_root/images/{train,val,test}/."""
    direct = data_root / "images" / file_name
    if direct.exists():
        return direct
    for split in ("train", "val", "test"):
        candidate = data_root / "images" / split / Path(file_name).name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Image not found for {file_name!r} under {data_root / 'images'}")


def write_dataset_yaml(
    yaml_path: Path,
    data_root: Path,
    nc: int,
    names: list[str],
    *,
    train: str = "images/train",
    val: str = "images/val",
    test: str = "images/test",
) -> None:
    """Write an Ultralytics-compatible dataset.yaml.

    Expects images and labels under parallel paths relative to data_root.
    """
    data = {
        "path": str(Path(data_root).resolve()),
        "train": train,
        "val": val,
        "test": test,
        "nc": nc,
        "names": names,
    }
    Path(yaml_path).write_text(yaml.dump(data, sort_keys=False, allow_unicode=True))


def build_specialist_yolo_dataset(
    specialist_ann: Path,
    data_root: Path,
    class_name: str,
    *,
    seed: int = 42,
    val_frac: float = 0.2,
    force: bool = True,
) -> Path:
    """Build a train/val YOLO dataset for one specialist model.

    Creates data_root/specialist/{class}/ with symlinked images and .txt labels
    for only the images present in specialist_ann. Returns the specialist root.
    """
    coco = COCO(str(specialist_ann))
    image_ids = sorted(coco.imgs.keys())
    if not image_ids:
        raise ValueError(f"No images in specialist annotation: {specialist_ann}")

    rng = random.Random(seed)
    shuffled = image_ids.copy()
    rng.shuffle(shuffled)
    n_val = max(1, int(len(shuffled) * val_frac))
    split_ids = {
        "val": set(shuffled[:n_val]),
        "train": set(shuffled[n_val:]) or set(shuffled[:1]),
    }
    if not split_ids["train"]:
        split_ids["train"] = split_ids["val"]

    run_name = class_name.replace("-", "_")
    specialist_root = Path(data_root) / "specialist" / run_name

    for split in ("train", "val"):
        img_dir = specialist_root / "images" / split
        lbl_dir = specialist_root / "labels" / split
        if force and img_dir.exists():
            shutil.rmtree(img_dir)
        if force and lbl_dir.exists():
            shutil.rmtree(lbl_dir)
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for img_id in split_ids[split]:
            img_info = coco.imgs[img_id]
            src = resolve_image_path(data_root, img_info["file_name"])
            dst = img_dir / src.name
            if not dst.exists():
                try:
                    dst.symlink_to(src.resolve())
                except OSError:
                    shutil.copy2(src, dst)

            w_img = img_info["width"]
            h_img = img_info["height"]
            ann_ids = coco.getAnnIds(imgIds=img_id)
            anns = coco.loadAnns(ann_ids)
            lines = []
            for ann in anns:
                x, y, w, h = ann["bbox"]
                cx = (x + w / 2) / w_img
                cy = (y + h / 2) / h_img
                nw = w / w_img
                nh = h / h_img
                cls_id = ann["category_id"] - 1
                lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
            (lbl_dir / f"{src.stem}.txt").write_text("\n".join(lines))

    return specialist_root
