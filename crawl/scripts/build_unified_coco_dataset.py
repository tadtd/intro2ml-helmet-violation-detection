from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


TARGET_CATEGORIES = [
  {"id": 1, "name": "motorbike", "supercategory": "vehicle"},
  {"id": 2, "name": "helmet", "supercategory": "safety"},
  {"id": 3, "name": "non-helmet", "supercategory": "violation"},
]
TARGET_NAME_TO_ID = {c["name"]: c["id"] for c in TARGET_CATEGORIES}
SPLITS = ["train", "val", "test"]
SPLIT_RATIOS = {"train": 0.7, "val": 0.1, "test": 0.2}


@dataclass
class RawSource:
  name: str
  annotation_path: Path
  image_root: Path
  source_split: str
  source_kind: str


@dataclass
class ObjectRecord:
  category: str
  bbox: tuple[float, float, float, float]  # xywh


@dataclass
class ImageRecord:
  source_name: str
  source_split: str
  source_kind: str
  source_file_name: str
  source_image_id: int
  file_path: Path
  width: int
  height: int
  video_name: str | None
  timestamp_s: float | None
  objects: list[ObjectRecord] = field(default_factory=list)
  group_key: str = ""


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description="Build unified 3-class COCO dataset for helmet violation detection."
  )
  parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
  parser.add_argument(
      "--output-root",
      type=Path,
      default=Path("data/processed/helmet_violation_coco"),
  )
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--near-duplicate-threshold", type=int, default=4)
  return parser.parse_args()


def discover_sources(raw_root: Path) -> list[RawSource]:
  sources: list[RawSource] = []
  dataset_dirs = [
      "CS114_helmet_detection_Final.v1i.coco",
      "helmet detection.v1i.coco",
      "Helmet Detection.v1i.coco (1)",
      "Motobike Detection.v1i.coco",
  ]

  for dataset_dir in dataset_dirs:
      dataset_path = raw_root / dataset_dir
      if not dataset_path.exists():
          continue
      for ann_path in sorted(dataset_path.glob("*/_annotations.coco.json")):
          split_name = ann_path.parent.name
          sources.append(
              RawSource(
                  name=dataset_dir,
                  annotation_path=ann_path,
                  image_root=ann_path.parent,
                  source_split=split_name,
                  source_kind="roboflow",
              )
          )

  grounding_ann = (
      raw_root
      / "grounding_dino_no_helmet"
      / "annotations"
      / "instances_no_helmet_grounding_dino.json"
  )
  grounding_images = raw_root / "grounding_dino_no_helmet" / "images"
  if grounding_ann.exists() and grounding_images.exists():
      sources.append(
          RawSource(
              name="grounding_dino_no_helmet",
              annotation_path=grounding_ann,
              image_root=grounding_images,
              source_split="grounding",
              source_kind="grounding",
          )
      )

  return sources


def normalize_text(text: str) -> str:
  text = text.lower().strip()
  text = text.replace("_", " ").replace("-", " ")
  text = re.sub(r"[^a-z0-9 ]+", " ", text)
  text = re.sub(r"\s+", " ", text).strip()
  return text


def canonicalize_category(name: str, category_id: int) -> str | None:
  if category_id == 0:
      return None

  text = normalize_text(name)
  if not text:
      return None

  non_helmet_markers = [
      "no helmet",
      "no helmets",
      "without helmet",
      "non helmet",
      "nohelmet",
      "no helmet rider",
  ]
  if any(marker in text for marker in non_helmet_markers):
      return "non-helmet"

  if "no" in text and "helmet" in text:
      return "non-helmet"

  if any(token in text for token in ["person", "people", "human", "rider"]):
      return None

  if any(
      token in text
      for token in ["motorbike", "motobike", "motorcycle", "motocycle", "scooter", "moped"]
  ):
      return "motorbike"

  if "helmet" in text:
      return "helmet"

  return None


def safe_float(value: Any) -> float | None:
  try:
      return float(value)
  except (TypeError, ValueError):
      return None


def parse_bbox_xywh(bbox: Any) -> tuple[float, float, float, float] | None:
  if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
      return None
  x = safe_float(bbox[0])
  y = safe_float(bbox[1])
  w = safe_float(bbox[2])
  h = safe_float(bbox[3])
  if x is None or y is None or w is None or h is None:
      return None
  if w <= 0 or h <= 0:
      return None
  return (x, y, w, h)


def clip_bbox_xywh(
  bbox: tuple[float, float, float, float], width: int, height: int
) -> tuple[float, float, float, float] | None:
  x, y, w, h = bbox
  if width <= 0 or height <= 0:
      return None

  x = max(0.0, min(x, float(width - 1)))
  y = max(0.0, min(y, float(height - 1)))
  w = max(0.0, min(w, float(width) - x))
  h = max(0.0, min(h, float(height) - y))

  if w <= 1.0 or h <= 1.0:
      return None

  return (round(x, 3), round(y, 3), round(w, 3), round(h, 3))


def load_grounding_whitelist(raw_root: Path) -> set[str]:
  images_dir = raw_root / "grounding_dino_no_helmet" / "images"
  whitelist: set[str] = set()
  if not images_dir.exists():
      return whitelist

  for image_path in images_dir.iterdir():
      if image_path.is_file():
          whitelist.add(image_path.name)
  return whitelist


def collect_records(sources: list[RawSource], grounding_whitelist: set[str]) -> tuple[list[ImageRecord], dict[str, Any]]:
  stats: dict[str, Any] = {
      "sources_loaded": 0,
      "images_seen": 0,
      "images_kept": 0,
      "images_missing": 0,
      "images_without_target_objects": 0,
      "annotations_seen": 0,
      "annotations_kept": 0,
      "annotations_dropped_invalid_bbox": 0,
      "annotations_dropped_category": 0,
      "dropped_categories": Counter(),
      "grounding_images_whitelisted": len(grounding_whitelist),
      "grounding_images_kept": 0,
  }

  all_records: list[ImageRecord] = []

  for source in sources:
      with source.annotation_path.open("r", encoding="utf-8") as f:
          coco = json.load(f)

      stats["sources_loaded"] += 1

      categories = coco.get("categories", [])
      category_name_by_id: dict[int, str] = {}
      category_map: dict[int, str | None] = {}
      for cat in categories:
          cat_id = int(cat.get("id"))
          cat_name = str(cat.get("name", ""))
          category_name_by_id[cat_id] = cat_name
          category_map[cat_id] = canonicalize_category(cat_name, cat_id)

      image_map: dict[int, ImageRecord] = {}
      for image_item in coco.get("images", []):
          stats["images_seen"] += 1
          image_id = int(image_item.get("id"))
          file_name = str(image_item.get("file_name", "")).strip()
          if not file_name:
              continue

          if source.source_kind == "grounding" and file_name not in grounding_whitelist:
              continue

          file_path = source.image_root / file_name
          if not file_path.exists():
              stats["images_missing"] += 1
              continue

          width = int(image_item.get("width") or 0)
          height = int(image_item.get("height") or 0)
          timestamp = safe_float(image_item.get("timestamp_s"))
          video_name = image_item.get("video_name")
          if video_name is not None:
              video_name = str(video_name)

          image_map[image_id] = ImageRecord(
              source_name=source.name,
              source_split=source.source_split,
              source_kind=source.source_kind,
              source_file_name=file_name,
              source_image_id=image_id,
              file_path=file_path,
              width=width,
              height=height,
              video_name=video_name,
              timestamp_s=timestamp,
          )

      for ann in coco.get("annotations", []):
          stats["annotations_seen"] += 1
          image_id = int(ann.get("image_id"))
          if image_id not in image_map:
              continue

          category_id = int(ann.get("category_id"))
          mapped_category = category_map.get(category_id)
          if mapped_category is None:
              stats["annotations_dropped_category"] += 1
              category_name = category_name_by_id.get(category_id, f"unknown_{category_id}")
              stats["dropped_categories"][category_name] += 1
              continue

          parsed_bbox = parse_bbox_xywh(ann.get("bbox"))
          if parsed_bbox is None:
              stats["annotations_dropped_invalid_bbox"] += 1
              continue

          image_map[image_id].objects.append(
              ObjectRecord(category=mapped_category, bbox=parsed_bbox)
          )
          stats["annotations_kept"] += 1

      for record in image_map.values():
          if not record.objects:
              stats["images_without_target_objects"] += 1
              continue
          if source.source_kind == "grounding":
              stats["grounding_images_kept"] += 1
          all_records.append(record)
          stats["images_kept"] += 1

  stats["dropped_categories"] = dict(stats["dropped_categories"])
  return all_records, stats


def md5_file(path: Path) -> str:
  hasher = hashlib.md5()
  with path.open("rb") as f:
      while True:
          chunk = f.read(1024 * 1024)
          if not chunk:
              break
          hasher.update(chunk)
  return hasher.hexdigest()


def average_hash_int(path: Path, hash_size: int = 8) -> tuple[int, int, int]:
    with Image.open(path) as image:
        image = image.convert("L")
        width, height = image.size
        image = image.resize((hash_size, hash_size), Image.Resampling.BILINEAR)
        pixels = list(image.tobytes())

    avg = sum(pixels) / len(pixels)
    bits = 0
    for pixel in pixels:
        bits = (bits << 1) | (1 if pixel > avg else 0)
    return bits, width, height


def hamming_distance(a: int, b: int) -> int:
        return (a ^ b).bit_count()


def object_key(category: str, bbox: tuple[float, float, float, float]) -> tuple[Any, ...]:
    return (
        category,
        round(bbox[0], 1),
        round(bbox[1], 1),
        round(bbox[2], 1),
        round(bbox[3], 1),
    )


def infer_sequence_pattern(file_name: str) -> str:
    stem = Path(file_name).stem
    if ".rf." in stem:
        stem = stem.split(".rf.", 1)[0]
    stem = re.sub(r"(_jpg|_jpeg|_png)$", "", stem, flags=re.IGNORECASE)
    tokens = [tok for tok in re.split(r"[^a-zA-Z0-9]+", stem) if tok]
    if not tokens:
        return "misc"

    first = tokens[0]
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", first)
    if match:
        prefix = match.group(1).lower()
        number = int(match.group(2))
        return f"{prefix}_{number:06d}"

    if len(tokens) >= 2 and tokens[1].isdigit():
        return f"{tokens[0].lower()}_{int(tokens[1]):06d}"

    if tokens[-1].isdigit():
        return f"{tokens[0].lower()}_{int(tokens[-1]):06d}"

    return "_".join(tok.lower() for tok in tokens[:3])


def build_group_key(record: ImageRecord) -> str:
    if record.video_name:
        if record.timestamp_s is not None:
            time_bucket = int(record.timestamp_s // 10)
            return (
                f"video_chunk::{record.source_name}::{record.video_name}::{time_bucket:05d}"
            )
        return f"video::{record.source_name}::{record.video_name}"
    pattern = infer_sequence_pattern(record.source_file_name)
    return f"pattern::{record.source_name}::{record.source_split}::{pattern}"


def deduplicate_records(
  records: list[ImageRecord], near_duplicate_threshold: int
) -> tuple[list[ImageRecord], dict[str, Any]]:
  stats: dict[str, Any] = {
      "input_images": len(records),
      "kept_images": 0,
      "exact_duplicates_removed": 0,
      "near_duplicates_removed": 0,
      "images_unreadable": 0,
      "objects_after_clip": 0,
      "objects_removed_after_clip": 0,
  }

  md5_to_index: dict[str, int] = {}
  canonical_hashes: list[int] = []
  canonical_records: list[ImageRecord] = []
  canonical_object_keys: list[set[tuple[Any, ...]]] = []

  for record in records:
      try:
          file_md5 = md5_file(record.file_path)
          phash, width, height = average_hash_int(record.file_path)
      except Exception:
          stats["images_unreadable"] += 1
          continue

      clipped_objects: list[ObjectRecord] = []
      for obj in record.objects:
          clipped = clip_bbox_xywh(obj.bbox, width, height)
          if clipped is None:
              stats["objects_removed_after_clip"] += 1
              continue
          clipped_objects.append(ObjectRecord(category=obj.category, bbox=clipped))

      if not clipped_objects:
          continue

      record.width = width
      record.height = height
      record.objects = clipped_objects
      stats["objects_after_clip"] += len(clipped_objects)

      if file_md5 in md5_to_index:
          canonical_idx = md5_to_index[file_md5]
          keys = canonical_object_keys[canonical_idx]
          for obj in record.objects:
              key = object_key(obj.category, obj.bbox)
              if key not in keys:
                  keys.add(key)
                  canonical_records[canonical_idx].objects.append(obj)
          stats["exact_duplicates_removed"] += 1
          continue

      near_duplicate_idx = None
      for idx, existing_hash in enumerate(canonical_hashes):
          if hamming_distance(phash, existing_hash) <= near_duplicate_threshold:
              near_duplicate_idx = idx
              break

      if near_duplicate_idx is not None:
          stats["near_duplicates_removed"] += 1
          continue

      record.group_key = build_group_key(record)
      canonical_records.append(record)
      canonical_hashes.append(phash)
      md5_to_index[file_md5] = len(canonical_records) - 1
      canonical_object_keys.append({object_key(obj.category, obj.bbox) for obj in record.objects})

  stats["kept_images"] = len(canonical_records)
  return canonical_records, stats


def assign_groups_to_splits(records: list[ImageRecord], seed: int) -> dict[int, str]:
    random_gen = random.Random(seed)

    groups: dict[str, list[int]] = defaultdict(list)
    for idx, record in enumerate(records):
        groups[record.group_key].append(idx)

    image_presence: list[set[str]] = []
    global_class_presence = Counter()
    for record in records:
        presence = {obj.category for obj in record.objects}
        image_presence.append(presence)
        for class_name in presence:
            global_class_presence[class_name] += 1

    group_items: list[tuple[str, list[int], Counter]] = []
    for group_key, indices in groups.items():
        class_counter = Counter()
        for index in indices:
            for class_name in image_presence[index]:
                class_counter[class_name] += 1
        group_items.append((group_key, indices, class_counter))

    random_gen.shuffle(group_items)
    group_items.sort(key=lambda item: len(item[1]), reverse=True)

    total_images = len(records)
    target_images = {
        "train": int(round(total_images * SPLIT_RATIOS["train"])),
        "val": int(round(total_images * SPLIT_RATIOS["val"])),
    }
    target_images["test"] = total_images - target_images["train"] - target_images["val"]

    target_class_counts: dict[str, dict[str, float]] = {split: {} for split in SPLITS}
    for split in SPLITS:
        for class_name in TARGET_NAME_TO_ID:
            target_class_counts[split][class_name] = (
                global_class_presence[class_name] * SPLIT_RATIOS[split]
            )

    assigned_split_by_group: dict[str, str] = {}
    current_images = Counter({split: 0 for split in SPLITS})
    current_class_counts = {
        split: Counter({class_name: 0 for class_name in TARGET_NAME_TO_ID})
        for split in SPLITS
    }

    def split_score(split: str, group_size: int, group_class_counts: Counter) -> float:
        new_image_count = current_images[split] + group_size
        target_image_count = max(1, target_images[split])
        image_score = abs(new_image_count - target_image_count) / target_image_count

        class_score_parts: list[float] = []
        for class_name in TARGET_NAME_TO_ID:
            target_count = max(1.0, target_class_counts[split][class_name])
            new_count = current_class_counts[split][class_name] + group_class_counts[class_name]
            class_score_parts.append(abs(new_count - target_count) / target_count)
        class_score = sum(class_score_parts) / len(class_score_parts)

        overflow = max(0.0, new_image_count - target_image_count)
        overflow_penalty = (overflow / target_image_count) * 12.0

        return image_score * 0.95 + class_score * 0.05 + overflow_penalty

    for group_key, indices, class_counts in group_items:
        group_size = len(indices)
        scored_splits = [(split, split_score(split, group_size, class_counts)) for split in SPLITS]
        scored_splits.sort(key=lambda item: item[1])
        best_split = scored_splits[0][0]

        assigned_split_by_group[group_key] = best_split
        current_images[best_split] += group_size
        for class_name in TARGET_NAME_TO_ID:
            current_class_counts[best_split][class_name] += class_counts[class_name]

    group_lists_by_split: dict[str, list[str]] = {split: [] for split in SPLITS}
    for group_key, split in assigned_split_by_group.items():
        group_lists_by_split[split].append(group_key)

    for split in SPLITS:
        if group_lists_by_split[split]:
            continue
        donor_split = max(SPLITS, key=lambda s: len(group_lists_by_split[s]))
        if not group_lists_by_split[donor_split]:
            continue
        donor_group = group_lists_by_split[donor_split].pop()
        assigned_split_by_group[donor_group] = split
        group_lists_by_split[split].append(donor_group)

    def split_size(split: str) -> int:
        return sum(len(groups[group_key]) for group_key in group_lists_by_split[split])

    # Rebalance to improve image-count adherence while preserving group boundaries.
    for _ in range(500):
        train_size = split_size("train")
        train_target = target_images["train"]
        if train_size >= train_target:
            break

        donor_candidates = [
            split for split in ["val", "test"] if split_size(split) > target_images[split]
        ]
        if not donor_candidates:
            break

        donor_split = max(
            donor_candidates,
            key=lambda split: split_size(split) - target_images[split],
        )
        donor_groups = group_lists_by_split[donor_split]
        if not donor_groups:
            break

        deficit = train_target - train_size
        donor_groups_sorted = sorted(donor_groups, key=lambda group_key: len(groups[group_key]))
        move_group = None
        for group_key in donor_groups_sorted:
            if len(groups[group_key]) <= deficit:
                move_group = group_key
                break
        if move_group is None:
            move_group = donor_groups_sorted[0]

        group_lists_by_split[donor_split].remove(move_group)
        group_lists_by_split["train"].append(move_group)
        assigned_split_by_group[move_group] = "train"

    for _ in range(500):
        val_delta = split_size("val") - target_images["val"]
        test_delta = split_size("test") - target_images["test"]

        if abs(val_delta) <= 1 and abs(test_delta) <= 1:
            break

        if val_delta > 0 and test_delta < 0:
            donor_split, recv_split = "val", "test"
        elif test_delta > 0 and val_delta < 0:
            donor_split, recv_split = "test", "val"
        else:
            break

        donor_groups = group_lists_by_split[donor_split]
        if not donor_groups:
            break

        donor_groups_sorted = sorted(donor_groups, key=lambda group_key: len(groups[group_key]))
        move_group = donor_groups_sorted[0]
        group_lists_by_split[donor_split].remove(move_group)
        group_lists_by_split[recv_split].append(move_group)
        assigned_split_by_group[move_group] = recv_split

    split_assignment_by_index: dict[int, str] = {}
    for idx, record in enumerate(records):
        split_assignment_by_index[idx] = assigned_split_by_group[record.group_key]

    return split_assignment_by_index


def sanitize_name(value: str) -> str:
  clean = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
  return clean.lower() or "source"


def build_split_coco(records: list[ImageRecord], split_name: str) -> dict[str, Any]:
  info = {
      "description": "Unified helmet violation dataset",
      "version": "1.0",
      "year": datetime.now(timezone.utc).year,
      "date_created": datetime.now(timezone.utc).isoformat(),
      "split": split_name,
  }
  return {
      "info": info,
      "licenses": [],
      "categories": TARGET_CATEGORIES,
      "images": [],
      "annotations": [],
  }


def export_dataset(
  records: list[ImageRecord],
  split_assignment: dict[int, str],
  output_root: Path,
) -> dict[str, Any]:
  images_root = output_root / "images"
  annotations_root = output_root / "annotations"
  reports_root = output_root / "reports"

  if output_root.exists():
      shutil.rmtree(output_root)

  for split in SPLITS:
      (images_root / split).mkdir(parents=True, exist_ok=True)
  annotations_root.mkdir(parents=True, exist_ok=True)
  reports_root.mkdir(parents=True, exist_ok=True)

  split_records: dict[str, list[tuple[int, ImageRecord]]] = {split: [] for split in SPLITS}
  for idx, record in enumerate(records):
      split = split_assignment[idx]
      split_records[split].append((idx, record))

  summary: dict[str, Any] = {
      "output_root": str(output_root),
      "splits": {},
      "global": {
          "images": len(records),
          "annotations": 0,
          "class_counts": {name: 0 for name in TARGET_NAME_TO_ID},
          "image_presence": {name: 0 for name in TARGET_NAME_TO_ID},
          "source_images": {},
      },
      "created_at": datetime.now(timezone.utc).isoformat(),
  }

  manifest_rows: list[dict[str, Any]] = []

  for split in SPLITS:
      coco = build_split_coco([record for _, record in split_records[split]], split)
      image_id = 1
      ann_id = 1
      split_class_counts = Counter({name: 0 for name in TARGET_NAME_TO_ID})
      split_presence_counts = Counter({name: 0 for name in TARGET_NAME_TO_ID})

      for idx, record in split_records[split]:
          source_slug = sanitize_name(record.source_name)
          extension = record.file_path.suffix.lower() or ".jpg"
          out_file_name = f"{idx + 1:07d}_{source_slug}{extension}"
          out_path = images_root / split / out_file_name
          shutil.copy2(record.file_path, out_path)

          coco["images"].append(
              {
                  "id": image_id,
                  "file_name": out_file_name,
                  "width": record.width,
                  "height": record.height,
                  "source_name": record.source_name,
                  "source_split": record.source_split,
                  "source_file_name": record.source_file_name,
                  "video_name": record.video_name,
                  "timestamp_s": record.timestamp_s,
                  "group_key": record.group_key,
              }
          )

          present_classes = {obj.category for obj in record.objects}
          for class_name in present_classes:
              split_presence_counts[class_name] += 1

          for obj in record.objects:
              category_id = TARGET_NAME_TO_ID[obj.category]
              x, y, w, h = obj.bbox
              coco["annotations"].append(
                  {
                      "id": ann_id,
                      "image_id": image_id,
                      "category_id": category_id,
                      "bbox": [x, y, w, h],
                      "area": round(w * h, 3),
                      "iscrowd": 0,
                  }
              )
              split_class_counts[obj.category] += 1
              ann_id += 1

          manifest_rows.append(
              {
                  "split": split,
                  "output_file_name": out_file_name,
                  "source_name": record.source_name,
                  "source_split": record.source_split,
                  "source_file_name": record.source_file_name,
                  "source_path": str(record.file_path),
                  "group_key": record.group_key,
                  "video_name": record.video_name or "",
                  "width": record.width,
                  "height": record.height,
                  "objects": len(record.objects),
                  "has_motorbike": int("motorbike" in present_classes),
                  "has_helmet": int("helmet" in present_classes),
                  "has_non_helmet": int("non-helmet" in present_classes),
              }
          )

          image_id += 1

      annotations_path = annotations_root / f"instances_{split}.json"
      with annotations_path.open("w", encoding="utf-8") as f:
          json.dump(coco, f, ensure_ascii=False, indent=2)

      summary["splits"][split] = {
          "images": len(coco["images"]),
          "annotations": len(coco["annotations"]),
          "class_counts": dict(split_class_counts),
          "image_presence": dict(split_presence_counts),
          "annotation_path": str(annotations_path),
      }

      summary["global"]["annotations"] += len(coco["annotations"])
      for class_name in TARGET_NAME_TO_ID:
          summary["global"]["class_counts"][class_name] += split_class_counts[class_name]
          summary["global"]["image_presence"][class_name] += split_presence_counts[class_name]

  source_counts = Counter(record.source_name for record in records)
  summary["global"]["source_images"] = dict(source_counts)

  summary_path = reports_root / "summary.json"
  with summary_path.open("w", encoding="utf-8") as f:
      json.dump(summary, f, ensure_ascii=False, indent=2)

  manifest_path = reports_root / "manifest.jsonl"
  with manifest_path.open("w", encoding="utf-8") as f:
      for row in manifest_rows:
          f.write(json.dumps(row, ensure_ascii=False) + "\n")

  return summary


def validate_exports(output_root: Path) -> dict[str, Any]:
  annotations_root = output_root / "annotations"
  images_root = output_root / "images"

  validation: dict[str, Any] = {
      "files_missing": [],
      "invalid_bboxes": 0,
      "orphan_annotations": 0,
      "invalid_categories": 0,
      "split_overlaps": 0,
  }

  split_files: dict[str, set[str]] = {split: set() for split in SPLITS}

  for split in SPLITS:
    ann_path = annotations_root / f"instances_{split}.json"
    with ann_path.open("r", encoding="utf-8") as f:
      coco = json.load(f)

    image_by_id = {int(item["id"]): item for item in coco.get("images", [])}
    for item in coco.get("images", []):
      file_name = str(item["file_name"])
      split_files[split].add(file_name)
      if not (images_root / split / file_name).exists():
        validation["files_missing"].append(str(images_root / split / file_name))

    valid_category_ids = set(TARGET_NAME_TO_ID.values())
    for ann in coco.get("annotations", []):
      if int(ann.get("image_id")) not in image_by_id:
        validation["orphan_annotations"] += 1

      if int(ann.get("category_id")) not in valid_category_ids:
        validation["invalid_categories"] += 1

      bbox = ann.get("bbox", [])
      if not isinstance(bbox, list) or len(bbox) < 4:
        validation["invalid_bboxes"] += 1
        continue
      if float(bbox[2]) <= 1.0 or float(bbox[3]) <= 1.0:
        validation["invalid_bboxes"] += 1

  split_pairs = [("train", "val"), ("train", "test"), ("val", "test")]
  for left, right in split_pairs:
    overlap = split_files[left].intersection(split_files[right])
    validation["split_overlaps"] += len(overlap)

  validation["files_missing"] = validation["files_missing"][:25]
  return validation


def main() -> None:
  args = parse_args()
  raw_root: Path = args.raw_root
  output_root: Path = args.output_root
  seed: int = args.seed
  near_duplicate_threshold: int = args.near_duplicate_threshold

  sources = discover_sources(raw_root)
  if not sources:
      raise SystemExit("No source annotations discovered. Check data/raw structure.")

  grounding_whitelist = load_grounding_whitelist(raw_root)
  records, collect_stats = collect_records(sources, grounding_whitelist)
  if not records:
      raise SystemExit("No records with target classes found after normalization/filtering.")

  dedup_records, dedup_stats = deduplicate_records(records, near_duplicate_threshold)
  if not dedup_records:
      raise SystemExit("No records left after deduplication.")

  split_assignment = assign_groups_to_splits(dedup_records, seed)
  summary = export_dataset(dedup_records, split_assignment, output_root)

  validation = validate_exports(output_root)
  full_report = {
      "config": {
          "raw_root": str(raw_root),
          "output_root": str(output_root),
          "seed": seed,
          "near_duplicate_threshold": near_duplicate_threshold,
      },
      "collect_stats": collect_stats,
      "dedup_stats": dedup_stats,
      "summary": summary,
      "validation": validation,
  }

  report_path = output_root / "reports" / "build_report.json"
  with report_path.open("w", encoding="utf-8") as f:
      json.dump(full_report, f, ensure_ascii=False, indent=2)

  print("Build completed.")
  print(json.dumps({"output_root": str(output_root), "report": str(report_path)}, indent=2))


if __name__ == "__main__":
  main()
