"""
Bước 7: Chuyển đổi pseudo-label (COCO JSON) sang định dạng YOLO.

Đầu vào : data/pseudo_labels/pseudo_instances_all.json
Đầu ra  :
  dataset/labels/{train,val,test}/<stem>.txt  — nhãn YOLO mỗi ảnh
  dataset/dataset.yaml                         — config sẵn cho YOLOv8/v11

Định dạng YOLO mỗi dòng trong .txt:
  <class_id> <x_center> <y_center> <width> <height>   (tất cả đã chuẩn hóa 0–1)

Mapping class:
  motorbike  (COCO id=1) → YOLO class 0
  helmet     (COCO id=2) → YOLO class 1
  no_helmet  (COCO id=3) → YOLO class 2
"""

import json
from pathlib import Path

IN_COCO_JSON = Path("data/pseudo_labels/pseudo_instances_all.json")
DATASET_DIR = Path("dataset")
LABELS_DIR = DATASET_DIR / "labels"
IMAGES_DIR = DATASET_DIR / "images"
OUT_YAML = DATASET_DIR / "dataset.yaml"

# COCO category_id → YOLO class index
CATEGORY_TO_CLASS: dict[int, int] = {1: 0, 2: 1, 3: 2}
CLASS_NAMES = ["motorbike", "helmet", "no_helmet"]


def _coco_bbox_to_yolo(bbox: list[float], img_w: int, img_h: int) -> tuple[float, float, float, float]:
    """Chuyển [x_min, y_min, w, h] (pixel) → (x_c, y_c, w, h) chuẩn hóa."""
    x_min, y_min, bw, bh = bbox
    x_c = (x_min + bw / 2.0) / img_w
    y_c = (y_min + bh / 2.0) / img_h
    w_n = bw / img_w
    h_n = bh / img_h
    # Kẹp về [0, 1] để tránh giá trị ngoài biên do lỗi bbox
    x_c = max(0.0, min(1.0, x_c))
    y_c = max(0.0, min(1.0, y_c))
    w_n = max(0.0, min(1.0, w_n))
    h_n = max(0.0, min(1.0, h_n))
    return x_c, y_c, w_n, h_n


def _write_yaml(splits: list[str]) -> None:
    lines = [
        f"path: {DATASET_DIR.resolve().as_posix()}",
        f"train: images/train",
        f"val: images/val",
        f"test: images/test",
        "",
        f"nc: {len(CLASS_NAMES)}",
        "names:",
    ]
    for i, name in enumerate(CLASS_NAMES):
        lines.append(f"  {i}: {name}")
    OUT_YAML.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not IN_COCO_JSON.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {IN_COCO_JSON}. "
            "Hãy chạy pseudo_label_with_grounding_dino.py trước."
        )

    # Tạo thư mục labels
    splits = ["train", "val", "test"]
    for split in splits:
        (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)

    # Đọc COCO JSON
    data = json.loads(IN_COCO_JSON.read_text(encoding="utf-8"))
    coco_images: list[dict] = data.get("images", [])
    coco_anns: list[dict] = data.get("annotations", [])

    # Build lookup: image_id → image info
    id_to_img: dict[int, dict] = {img["id"]: img for img in coco_images}

    # Build lookup: image_id → list of annotations
    id_to_anns: dict[int, list[dict]] = {}
    for ann in coco_anns:
        id_to_anns.setdefault(ann["image_id"], []).append(ann)

    written = 0
    skipped = 0
    empty = 0

    for img_info in coco_images:
        img_id: int = img_info["id"]
        file_name: str = img_info["file_name"]
        img_w: int = img_info["width"]
        img_h: int = img_info["height"]
        split: str = img_info.get("split", "train")

        if split not in splits:
            split = "train"

        # Xác định vị trí file label
        stem = Path(file_name).stem
        label_path = LABELS_DIR / split / f"{stem}.txt"

        anns = id_to_anns.get(img_id, [])
        lines: list[str] = []

        for ann in anns:
            cat_id: int = ann.get("category_id", 0)
            cls = CATEGORY_TO_CLASS.get(cat_id)
            if cls is None:
                continue

            bbox: list[float] = ann.get("bbox", [])
            if len(bbox) != 4 or bbox[2] <= 0 or bbox[3] <= 0:
                continue

            x_c, y_c, w_n, h_n = _coco_bbox_to_yolo(bbox, img_w, img_h)
            lines.append(f"{cls} {x_c:.6f} {y_c:.6f} {w_n:.6f} {h_n:.6f}")

        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

        if lines:
            written += 1
        else:
            empty += 1

    # Viết dataset.yaml
    _write_yaml(splits)

    print(f"Labels đã ghi   : {written:,} ảnh có annotation")
    print(f"Labels rỗng     : {empty:,} ảnh không có detection")
    print(f"dataset.yaml    : {OUT_YAML}")
    print(f"Thư mục labels  : {LABELS_DIR}")
    print()
    print("Sẵn sàng train YOLOv8/v11:")
    print(f"  yolo train model=yolov8n.pt data={OUT_YAML} epochs=50 imgsz=640")


if __name__ == "__main__":
    main()
