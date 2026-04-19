"""
Pipeline tự động hoàn toàn:
  Crawl YouTube → Tải video → Trích xuất frame → Lọc frame →
  Chia dataset → Pseudo-label (Grounding DINO) → Convert sang YOLO → Train model

Cách dùng:
    # Chạy toàn bộ pipeline (bước 1–5, không có pseudo-label)
    uv run python run_pipeline.py

    # Chạy 100% tự động: crawl → label → sẵn sàng train (bước 1–7)
    uv run python run_pipeline.py --pseudo-labels

    # Bắt đầu từ bước 3 (bỏ qua crawl và download đã có sẵn)
    uv run python run_pipeline.py --from-step 3

    # Chỉ chạy từ bước 3 đến bước 4
    uv run python run_pipeline.py --from-step 3 --to-step 4

    # Tùy chỉnh ngưỡng pseudo-label
    uv run python run_pipeline.py --pseudo-labels --box-threshold 0.3 --no-helmet-min-score 0.45
"""

import argparse
import sys
import time
import traceback
from datetime import timedelta
from types import SimpleNamespace

import torch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_elapsed(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    total_sec = int(td.total_seconds())
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def _banner(text: str) -> None:
    line = "─" * 60
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}")


def _run_step(step_num: int, name: str, fn, *args, **kwargs) -> bool:
    """Chạy một bước pipeline. Trả về True nếu thành công."""
    _banner(f"BƯỚC {step_num}: {name}")
    t0 = time.perf_counter()
    try:
        fn(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        print(f"\n[OK] Bước {step_num} hoàn thành trong {_fmt_elapsed(elapsed)}")
        return True
    except Exception:
        elapsed = time.perf_counter() - t0
        print(f"\n[LỖI] Bước {step_num} thất bại sau {_fmt_elapsed(elapsed)}:")
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chạy toàn bộ pipeline chuẩn bị dataset helmet-violation detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--from-step",
        type=int,
        default=1,
        metavar="N",
        help="Bắt đầu từ bước N (1–6). Mặc định: 1",
    )
    parser.add_argument(
        "--to-step",
        type=int,
        default=None,
        metavar="N",
        help="Dừng lại sau bước N (1–6). Mặc định: 5 (hoặc 6 nếu --pseudo-labels được bật)",
    )
    parser.add_argument(
        "--pseudo-labels",
        action="store_true",
        help="Chạy thêm bước 6: pseudo-labeling bằng Grounding DINO (mặc định: tắt)",
    )
    # Pseudo-label options
    pl = parser.add_argument_group("Tùy chọn Grounding DINO (chỉ dùng với --pseudo-labels)")
    pl.add_argument("--model-id", default="IDEA-Research/grounding-dino-base")
    pl.add_argument("--box-threshold", type=float, default=0.28)
    pl.add_argument("--text-threshold", type=float, default=0.25)
    pl.add_argument("--no-helmet-min-score", type=float, default=0.40)
    pl.add_argument("--motorbike-min-score", type=float, default=0.30)
    pl.add_argument("--no-helmet-vs-helmet-ratio", type=float, default=1.05)
    pl.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Thiết bị PyTorch: 'cuda' hoặc 'cpu'. Mặc định: tự phát hiện",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    max_step = 7 if args.pseudo_labels else 5
    from_step = max(1, args.from_step)
    to_step = min(max_step, args.to_step) if args.to_step is not None else max_step

    if from_step > to_step:
        print(f"[LỖI] --from-step ({from_step}) lớn hơn --to-step ({to_step}). Không có bước nào được chạy.")
        sys.exit(1)

    print(f"\nPIPELINE: Chạy bước {from_step} → {to_step}")
    if args.pseudo_labels:
        print("Pseudo-labeling: BẬT")
    print(f"Device (PyTorch): {args.device}\n")

    pipeline_start = time.perf_counter()
    results: dict[int, bool] = {}

    # ------------------------------------------------------------------
    # Bước 1 – Thu thập link video từ YouTube
    # ------------------------------------------------------------------
    if from_step <= 1 <= to_step:
        from bot_collect_video_links import collect_youtube_links
        results[1] = _run_step(1, "Thu thập link video từ YouTube", collect_youtube_links)
        if not results[1]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 2 – Tải video về máy
    # ------------------------------------------------------------------
    if from_step <= 2 <= to_step:
        from download_videos import main as download_main
        results[2] = _run_step(2, "Tải video về máy", download_main)
        if not results[2]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 3 – Trích xuất frame từ video
    # ------------------------------------------------------------------
    if from_step <= 3 <= to_step:
        from extract_frames import main as extract_main
        results[3] = _run_step(3, "Trích xuất frame từ video", extract_main)
        if not results[3]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 4 – Lọc và chấm điểm frame
    # ------------------------------------------------------------------
    if from_step <= 4 <= to_step:
        from filter_frames import main as filter_main
        results[4] = _run_step(4, "Lọc và chấm điểm frame", filter_main)
        if not results[4]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 5 – Chia dataset train/val/test
    # ------------------------------------------------------------------
    if from_step <= 5 <= to_step:
        from prepare_dataset_for_annotation import main as prepare_main
        results[5] = _run_step(5, "Chia dataset train / val / test", prepare_main)
        if not results[5]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 6 – Pseudo-label với Grounding DINO (tùy chọn)
    # ------------------------------------------------------------------
    if args.pseudo_labels and from_step <= 6 <= to_step:
        from pseudo_label_with_grounding_dino import run as pseudo_run
        pseudo_args = SimpleNamespace(
            model_id=args.model_id,
            box_threshold=args.box_threshold,
            text_threshold=args.text_threshold,
            no_helmet_min_score=args.no_helmet_min_score,
            motorbike_min_score=args.motorbike_min_score,
            no_helmet_vs_helmet_ratio=args.no_helmet_vs_helmet_ratio,
            device=args.device,
        )
        results[6] = _run_step(
            6,
            "Pseudo-label với Grounding DINO",
            pseudo_run,
            pseudo_args,
        )
        if not results[6]:
            _abort(results, pipeline_start)

    # ------------------------------------------------------------------
    # Bước 7 – Chuyển pseudo-label sang định dạng YOLO
    # ------------------------------------------------------------------
    if args.pseudo_labels and from_step <= 7 <= to_step:
        from convert_to_yolo import main as yolo_main
        results[7] = _run_step(7, "Chuyển sang định dạng YOLO", yolo_main)

    # ------------------------------------------------------------------
    # Tổng kết + báo cáo dataset
    # ------------------------------------------------------------------
    _print_summary(results, pipeline_start)
    _print_dataset_report(args.pseudo_labels)


def _abort(results: dict, start: float) -> None:
    _print_summary(results, start)
    _print_dataset_report(pseudo_labels=False)
    sys.exit(1)


def _print_summary(results: dict, start: float) -> None:
    total = time.perf_counter() - start
    _banner("KẾT QUẢ PIPELINE")
    step_names = {
        1: "Thu thập link video",
        2: "Tải video",
        3: "Trích xuất frame",
        4: "Lọc frame",
        5: "Chia dataset",
        6: "Pseudo-label",
        7: "Convert sang YOLO",
    }
    all_ok = True
    for step, ok in sorted(results.items()):
        status = "[OK]  " if ok else "[LỖI]"
        print(f"  Bước {step} {status}  {step_names.get(step, '')}")
        if not ok:
            all_ok = False

    print(f"\nTổng thời gian: {_fmt_elapsed(total)}")
    if all_ok:
        print("Tất cả các bước đã hoàn thành thành công.")
    else:
        print("Một số bước bị lỗi. Kiểm tra log bên trên để biết chi tiết.")


def _print_dataset_report(pseudo_labels: bool = False) -> None:
    """In báo cáo thống kê dataset sau khi pipeline chạy xong."""
    from pathlib import Path

    dataset_meta = Path("dataset/images_metadata.csv")
    dataset_dir = Path("dataset/images")
    pseudo_review_dir = Path("dataset/pseudo_review/no_helmet")
    pseudo_csv = Path("data/pseudo_labels/pseudo_image_scores.csv")

    # Chỉ in nếu có dữ liệu để báo cáo
    has_dataset = dataset_meta.exists() or dataset_dir.exists()
    has_pseudo = pseudo_labels and (pseudo_review_dir.exists() or pseudo_csv.exists())
    if not has_dataset and not has_pseudo:
        return

    _banner("BÁO CÁO DATASET")

    # ── Thống kê ảnh theo split ──────────────────────────────────────
    if dataset_meta.exists():
        try:
            import pandas as pd
            df = pd.read_csv(dataset_meta)
            counts = df["split"].value_counts().to_dict() if "split" in df.columns else {}
            total_imgs = len(df)
            print(f"  Tổng số ảnh : {total_imgs:,}")
            for split in ("train", "val", "test"):
                n = counts.get(split, 0)
                pct = n / total_imgs * 100 if total_imgs else 0
                print(f"    {split:<6} : {n:>5,}  ({pct:.1f}%)")

            # Số nguồn video
            if "source_video" in df.columns:
                n_videos = df["source_video"].nunique()
                print(f"  Số video nguồn: {n_videos:,}")
        except Exception as e:
            print(f"  [!] Không đọc được {dataset_meta}: {e}")
    elif dataset_dir.exists():
        # Fallback: đếm file trực tiếp
        for split in ("train", "val", "test"):
            d = dataset_dir / split
            n = len(list(d.glob("*.*"))) if d.exists() else 0
            print(f"    {split:<6} : {n:>5,} ảnh")

    # ── Pseudo-label ─────────────────────────────────────────────────
    if has_pseudo:
        print()
        if pseudo_csv.exists():
            try:
                import pandas as pd
                pdf = pd.read_csv(pseudo_csv)
                total_pl = len(pdf)
                candidates = int(pdf["keep_no_helmet_candidate"].sum()) if "keep_no_helmet_candidate" in pdf.columns else 0
                print(f"  Pseudo-label  : {total_pl:,} ảnh đã xử lý, {candidates:,} candidate no-helmet")
            except Exception:
                pass

        if pseudo_review_dir.exists():
            review_imgs = list(pseudo_review_dir.rglob("*.jpg")) + list(pseudo_review_dir.rglob("*.png"))
            print(f"  Thư mục review: {pseudo_review_dir}  ({len(review_imgs):,} ảnh)")
            print("  → Xem lại ảnh trong thư mục review trước khi dùng làm nhãn huấn luyện.")

    # ── YOLO labels ──────────────────────────────────────────────────
    yolo_labels_dir = Path("dataset") / "labels"
    yolo_yaml = Path("dataset") / "dataset.yaml"
    if pseudo_labels and yolo_yaml.exists():
        print()
        label_count = sum(1 for _ in yolo_labels_dir.rglob("*.txt")) if yolo_labels_dir.exists() else 0
        print(f"  YOLO labels     : {label_count:,} file .txt trong {yolo_labels_dir}")
        print(f"  dataset.yaml    : {yolo_yaml}")
        print()
        print("  Sẵn sàng train — chạy lệnh sau:")
        print(f"    pip install ultralytics")
        print(f"    yolo train model=yolov8n.pt data={yolo_yaml} epochs=50 imgsz=640")

    # ── Bước tiếp theo ───────────────────────────────────────────────
    print()
    print("  Bước tiếp theo:")
    if pseudo_labels and yolo_yaml.exists():
        print("    • (Tùy chọn) Review ảnh trong dataset/pseudo_review/no_helmet/ để loại ảnh sai")
        print("    • Cài ultralytics: pip install ultralytics")
        print(f"    • Chạy train: yolo train model=yolov8n.pt data={yolo_yaml} epochs=50 imgsz=640")
    else:
        print("    • Kiểm tra ảnh trong dataset/images/{train,val,test}/")
        print("    • Tiến hành annotation thủ công (LabelImg / CVAT / Roboflow ...)")
        print("    • Hoặc chạy lại với --pseudo-labels để tự động hóa 100%")


if __name__ == "__main__":
    main()
