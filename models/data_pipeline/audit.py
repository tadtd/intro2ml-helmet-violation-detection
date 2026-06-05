"""Step 1 — Annotation Coverage Audit.

Loads instances_train.json and measures which classes each image has annotated.
Saves per-image coverage and image-ID lists used by subsequent pipeline steps.

Run:
    uv run python data_pipeline/audit.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
from pycocotools.coco import COCO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils import get_paths

# COCO category IDs for the three classes
CAT_MOTORBIKE  = 1
CAT_HELMET     = 2
CAT_NON_HELMET = 3
CAT_NAMES      = {1: "motorbike", 2: "helmet", 3: "non-helmet"}


def run_audit(data_root: Path, out_root: Path) -> dict:
    ann_path = data_root / "annotations" / "instances_train.json"
    audit_dir = out_root / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    coco = COCO(str(ann_path))

    rows = []
    fully_labeled_ids = []
    partial_ids = []
    missing_per_image: dict[str, list[str]] = {}

    for img_id, img_info in coco.imgs.items():
        ann_ids = coco.getAnnIds(imgIds=img_id)
        anns = coco.loadAnns(ann_ids)
        present_cats = {ann["category_id"] for ann in anns}

        has_motorbike  = CAT_MOTORBIKE  in present_cats
        has_helmet     = CAT_HELMET     in present_cats
        has_non_helmet = CAT_NON_HELMET in present_cats
        is_fully_labeled = has_motorbike and has_helmet and has_non_helmet

        rows.append({
            "image_id":        img_id,
            "file_name":       img_info["file_name"],
            "has_motorbike":   has_motorbike,
            "has_helmet":      has_helmet,
            "has_non_helmet":  has_non_helmet,
            "is_fully_labeled": is_fully_labeled,
        })

        if is_fully_labeled:
            fully_labeled_ids.append(img_id)
        else:
            partial_ids.append(img_id)
            missing = []
            if not has_motorbike:
                missing.append("motorbike")
            if not has_helmet:
                missing.append("helmet")
            if not has_non_helmet:
                missing.append("non-helmet")
            missing_per_image[str(img_id)] = missing

    df = pd.DataFrame(rows)
    total = len(df)
    n_full = len(fully_labeled_ids)
    n_partial = len(partial_ids)

    print("=" * 60)
    print("Annotation Coverage Report")
    print("=" * 60)
    print(f"Total training images    : {total:,}")
    print(f"Fully labeled (all 3)    : {n_full:,}  ({100 * n_full / total:.1f}%)")
    print(f"Partial (missing ≥1 cls) : {n_partial:,}  ({100 * n_partial / total:.1f}%)")
    print()

    combo_counts = df.groupby(
        ["has_motorbike", "has_helmet", "has_non_helmet"]
    ).size().reset_index(name="count")
    print("Coverage combinations:")
    for _, row in combo_counts.iterrows():
        flags = (
            ("motorbike" if row["has_motorbike"] else "-")
            + " / "
            + ("helmet" if row["has_helmet"] else "-")
            + " / "
            + ("non-helmet" if row["has_non_helmet"] else "-")
        )
        print(f"  {flags:<35} {row['count']:>5,}")
    print("=" * 60)

    # Save outputs
    df.to_csv(audit_dir / "coverage.csv", index=False)
    (audit_dir / "fully_labeled_ids.json").write_text(json.dumps(fully_labeled_ids))
    (audit_dir / "partial_ids.json").write_text(json.dumps(partial_ids))
    (audit_dir / "missing_per_image.json").write_text(json.dumps(missing_per_image))

    print(f"\nOutputs saved to {audit_dir}")
    print(f"  coverage.csv            ({total} rows)")
    print(f"  fully_labeled_ids.json  ({n_full} IDs)")
    print(f"  partial_ids.json        ({n_partial} IDs)")
    print(f"  missing_per_image.json  ({n_partial} entries)")

    if n_partial == 0:
        print("\nAll images are fully labeled — data pipeline not needed.")
        print("Training can proceed directly on instances_train.json.")

    return {
        "total": total,
        "fully_labeled": n_full,
        "partial": n_partial,
    }


def main() -> None:
    data_root, out_root = get_paths()
    run_audit(data_root, out_root)


if __name__ == "__main__":
    main()
