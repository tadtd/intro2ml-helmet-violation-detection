import json
from pathlib import Path
from typing import Callable, Optional

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

    coco = COCO(str(ann_json))
    ann_stat = Path(ann_json).stat()
    source_info = {
        "annotation": str(Path(ann_json).resolve()),
        "size": ann_stat.st_size,
        "mtime_ns": ann_stat.st_mtime_ns,
        "image_count": len(coco.imgs),
    }
    marker = out_dir / ".source.json"
    existing_txt = list(out_dir.glob("*.txt"))

    if not force and marker.exists() and len(existing_txt) == len(coco.imgs):
        try:
            if json.loads(marker.read_text()) == source_info:
                return out_dir
        except json.JSONDecodeError:
            pass

    for txt in existing_txt:
        txt.unlink()

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

    marker.write_text(json.dumps(source_info, indent=2))
    return out_dir


def write_dataset_yaml(
    yaml_path: Path,
    data_root: Path,
    nc: int,
    names: list[str],
) -> None:
    """Write an Ultralytics-compatible dataset.yaml.

    Expects images at data_root/images/{train,val,test}/
    and labels at data_root/labels/{train,val,test}/ (parallel structure).
    """
    data = {
        "path": str(Path(data_root).resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": nc,
        "names": names,
    }
    Path(yaml_path).write_text(yaml.dump(data, sort_keys=False, allow_unicode=True))
