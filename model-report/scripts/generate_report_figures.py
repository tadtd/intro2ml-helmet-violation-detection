"""Generate report figures from saved YOLO, Faster R-CNN and RT-DETR artifacts.

Run from the repository root:
    uv run python "[Intro2ML] Model-Report/scripts/generate_report_figures.py"
"""

from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageDraw, ImageFont
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from ultralytics import RTDETR, YOLO


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "model-report"
IMG = REPORT / "img"
CLASSES = ["motorbike", "helmet", "non-helmet"]
# Measured on the test split by models/checkpoints/eval_per_class.py (one shared
# COCOeval for all three models). FPS comes from each model's recorded run on a
# Tesla T4. Keep these in sync with output/per_class_results.json.
COMPARISON_METRICS = {
    "YOLO": {"mAP@0.5": 0.582, "mAP@0.5:0.95": 0.389, "AR/Recall": 0.717, "FPS": 36.4},
    "Faster R-CNN": {"mAP@0.5": 0.650, "mAP@0.5:0.95": 0.423, "AR/Recall": 0.624, "FPS": 12.4},
    "RT-DETR": {"mAP@0.5": 0.555, "mAP@0.5:0.95": 0.369, "AR/Recall": 0.727, "FPS": 2.8},
}

# AP@0.5 per class — the numbers the combined mAP above hides.
PER_CLASS_AP50 = {
    "YOLO": {"motorbike": 0.518, "helmet": 0.590, "non-helmet": 0.636},
    "Faster R-CNN": {"motorbike": 0.779, "helmet": 0.558, "non-helmet": 0.613},
    "RT-DETR": {"motorbike": 0.445, "helmet": 0.575, "non-helmet": 0.646},
}
MODEL_COLORS = {"YOLO": "#2F80ED", "Faster R-CNN": "#27AE60", "RT-DETR": "#EB5757"}
BOX_COLORS = {"motorbike": "#2F80ED", "helmet": "#27AE60", "non-helmet": "#EB5757"}
FRCNN_NAMES = {1: "motorbike", 2: "helmet", 3: "non-helmet"}
INFERENCE_IMAGES = [
    "0003253_grounding_dino_no_helmet.jpg",
    "0003254_grounding_dino_no_helmet.jpg",
    "0002648_motobike_detection_v1i_coco.jpg",
]


def read_csv_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key, value in list(row.items()):
            try:
                row[key.strip()] = float(str(value).strip())
            except ValueError:
                row[key.strip()] = str(value).strip()
    return rows


def col(rows: list[dict], name: str) -> list[float]:
    return [float(row[name]) for row in rows]


def draw_arch(path: Path, title: str, boxes: list[str], note: str) -> None:
    fig, ax = plt.subplots(figsize=(5.8, 7.2), dpi=220)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    colors = ["#EAF3FA", "#F5ECD8", "#E7F4E6", "#F8E3E2", "#E8E2F3"]
    x, width, height = 0.14, 0.72, 0.105
    y0, step = 0.78, 0.135

    ax.text(0.5, 0.945, title, ha="center", va="center", fontsize=16, fontweight="bold")
    for i, text in enumerate(boxes):
        y = y0 - i * step
        rect = patches.FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.025,rounding_size=0.025",
            linewidth=1.8, edgecolor="#2F3337", facecolor=colors[i % len(colors)],
        )
        ax.add_patch(rect)
        ax.text(
            x + width / 2,
            y + height / 2,
            text,
            ha="center",
            va="center",
            fontsize=12.5,
            color="#222222",
        )
        if i < len(boxes) - 1:
            ax.annotate(
                "",
                xy=(0.5, y - 0.02),
                xytext=(0.5, y - step + height + 0.025),
                arrowprops=dict(arrowstyle="->", lw=1.8, color="#2F3337"),
            )

    ax.text(0.5, 0.055, note, ha="center", va="center", fontsize=10.5, color="#333333")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def ensure_dirs() -> None:
    for sub in ["common", "yolo", "fasterrcnn", "rtdetr"]:
        (IMG / sub).mkdir(parents=True, exist_ok=True)


def copy_existing_yolo_and_rtdetr_figures() -> None:
    eval_root = ROOT / "runs/detect/[Intro2ML] Model-Report/report_eval"
    copies = {
        eval_root / "yolo_test/confusion_matrix_normalized.png": IMG / "yolo/confusion_matrix_normalized.png",
        eval_root / "yolo_test/BoxPR_curve.png": IMG / "yolo/BoxPR_curve.png",
        ROOT / "yolo/yolo/yolo_final/val_batch0_labels.jpg": IMG / "yolo/val_batch0_labels.jpg",
        ROOT / "yolo/yolo/yolo_final/val_batch0_pred.jpg": IMG / "yolo/val_batch0_pred.jpg",
        eval_root / "rtdetr_test/confusion_matrix_normalized.png": IMG / "rtdetr/confusion_matrix_normalized.png",
        eval_root / "rtdetr_test/BoxPR_curve.png": IMG / "rtdetr/BoxPR_curve.png",
    }
    for src, dst in copies.items():
        if src.exists():
            shutil.copy2(src, dst)


def plot_common_dataset() -> None:
    ann_root = ROOT / "data/annotations"
    splits = [("Train", "instances_train_merged.json"), ("Validation", "instances_val.json"), ("Test", "instances_test.json")]
    image_counts, box_counts, source_counts = [], [], []
    for _, fname in splits:
        data = json.loads((ann_root / fname).read_text())
        image_counts.append(len(data["images"]))
        counts = {1: 0, 2: 0, 3: 0}
        for ann in data["annotations"]:
            counts[ann["category_id"]] += 1
        box_counts.append([counts[1], counts[2], counts[3]])
        src = Counter()
        for img in data["images"]:
            fn = img["file_name"]
            if "grounding_dino_no_helmet" in fn:
                src["grounding_dino"] += 1
            elif "motobike_detection" in fn:
                src["motobike_detection"] += 1
            elif "cs114" in fn:
                src["cs114"] += 1
            else:
                src["other"] += 1
        source_counts.append(src)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), dpi=180)
    axes[0].bar([s[0] for s in splits], image_counts)
    axes[0].set_title("Images by split")
    axes[0].set_ylabel("Number of images")
    x = np.arange(len(splits))
    width = 0.22
    for j, name in enumerate(CLASSES):
        axes[1].bar(x + (j - 1) * width, [row[j] for row in box_counts], width=width, label=name)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([s[0] for s in splits])
    axes[1].set_title("Bounding boxes by class")
    axes[1].legend(frameon=True)
    fig.tight_layout()
    fig.savefig(IMG / "common/dataset_distribution.png", bbox_inches="tight")
    plt.close(fig)

    all_sources = sorted(set().union(*[set(c.keys()) for c in source_counts]))
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=180)
    bottom = np.zeros(len(splits))
    for source in all_sources:
        vals = np.array([c.get(source, 0) for c in source_counts])
        ax.bar([s[0] for s in splits], vals, bottom=bottom, label=source)
        bottom += vals
    ax.set_title("Image sources by split")
    ax.set_ylabel("Number of images")
    ax.legend(frameon=True, fontsize=8)
    fig.tight_layout()
    fig.savefig(IMG / "common/dataset_sources.png", bbox_inches="tight")
    plt.close(fig)


def plot_yolo_curves() -> None:
    rows = read_csv_rows(ROOT / "yolo/yolo/yolo_final/results.csv")
    epochs = col(rows, "epoch")
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4), dpi=180)
    for ax, (title, train_c, val_c) in zip(axes, [
        ("Box loss", "train/box_loss", "val/box_loss"),
        ("Classification loss", "train/cls_loss", "val/cls_loss"),
        ("DFL loss", "train/dfl_loss", "val/dfl_loss"),
    ]):
        ax.plot(epochs, col(rows, train_c), label="Train", linewidth=2)
        ax.plot(epochs, col(rows, val_c), label="Validation", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.legend(frameon=True)
    fig.tight_layout()
    fig.savefig(IMG / "yolo/loss_curves_report.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=180)
    for label, c in [
        ("Precision", "metrics/precision(B)"),
        ("Recall", "metrics/recall(B)"),
        ("mAP@0.5", "metrics/mAP50(B)"),
        ("mAP@0.5:0.95", "metrics/mAP50-95(B)"),
    ]:
        ax.plot(epochs, col(rows, c), label=label, linewidth=2)
    ax.set_title("YOLO validation metrics during training")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.legend(frameon=True, ncol=2)
    fig.tight_layout()
    fig.savefig(IMG / "yolo/metrics_curves_report.png", bbox_inches="tight")
    plt.close(fig)


def plot_fasterrcnn_figures() -> None:
    rows = read_csv_rows(ROOT / "faster-rcn/faster-rcnn/fasterrcnn_learning_curves.csv")
    epochs = col(rows, "epoch")
    train_loss = np.array(col(rows, "train_loss"))
    val_loss = np.array(col(rows, "val_loss"))
    lr = np.array(col(rows, "lr"))
    gap = val_loss - train_loss

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), dpi=180)

    axes[0].plot(epochs, train_loss, label="Train", linewidth=2)
    axes[0].plot(epochs, val_loss, label="Validation", linewidth=2)
    axes[0].set_title("Train vs validation loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend(frameon=True)

    axes[1].plot(epochs, val_loss, color="#EB5757", linewidth=2)
    best_idx = int(np.argmin(val_loss))
    axes[1].scatter([epochs[best_idx]], [val_loss[best_idx]], color="#222222", zorder=3)
    axes[1].annotate(
        f"best epoch {int(epochs[best_idx])}\n{val_loss[best_idx]:.3f}",
        (epochs[best_idx], val_loss[best_idx]),
        textcoords="offset points",
        xytext=(12, 10),
        fontsize=8,
    )
    axes[1].set_title("Validation loss")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")

    axes[2].plot(epochs, gap, color="#9B51E0", linewidth=2)
    axes[2].axhline(0, color="#333333", linewidth=1, alpha=0.5)
    axes[2].set_title("Validation-train loss gap")
    axes[2].set_xlabel("Epoch")
    axes[2].set_ylabel("Loss gap")

    for ax in axes:
        ax.grid(True, linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(IMG / "fasterrcnn/loss_curves_report.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=180)
    ax.step(epochs, lr, where="post", color="#27AE60", linewidth=2.4)
    ax.set_title("Faster R-CNN learning-rate schedule")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Learning rate")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(IMG / "fasterrcnn/lr_schedule_report.png", bbox_inches="tight")
    plt.close(fig)

    with (ROOT / "faster-rcn/faster-rcnn/fasterrcnn_confusion_matrix.csv").open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)[1:]
        labels, matrix = [], []
        for row in reader:
            labels.append(row[0])
            matrix.append([int(x) for x in row[1:]])
    mat = np.array(matrix)
    norm = mat / np.maximum(mat.sum(axis=1, keepdims=True), 1)
    for data, filename, title, fmt in [
        (mat, "confusion_matrix.png", "Faster R-CNN confusion matrix on test", "{:.0f}"),
        (norm, "confusion_matrix_normalized.png", "Faster R-CNN normalized confusion matrix on test", "{:.2f}"),
    ]:
        fig, ax = plt.subplots(figsize=(6.7, 5.8), dpi=180)
        im = ax.imshow(data, cmap="Blues")
        ax.set_xticks(np.arange(len(header)))
        ax.set_xticklabels(header, rotation=35, ha="right")
        ax.set_yticks(np.arange(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Ground truth")
        ax.set_title(title)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                ax.text(j, i, fmt.format(data[i, j]), ha="center", va="center", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=.046, pad=.04)
        fig.tight_layout()
        fig.savefig(IMG / "fasterrcnn" / filename, bbox_inches="tight")
        plt.close(fig)


def plot_per_class_ap() -> None:
    """AP@0.5 grouped by class — shows what the averaged mAP hides.

    Faster R-CNN wins the combined mAP purely on `motorbike`; on `non-helmet`,
    the class the system exists to catch, the ranking reverses.
    """
    models = list(PER_CLASS_AP50)
    width = 0.26
    positions = range(len(CLASSES))

    fig, ax = plt.subplots(figsize=(8.2, 4.2), dpi=180)
    for offset, model in enumerate(models):
        values = [PER_CLASS_AP50[model][c] for c in CLASSES]
        bars = ax.bar(
            [p + (offset - 1) * width for p in positions],
            values,
            width=width,
            label=model,
            color=MODEL_COLORS[model],
        )
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_xticks(list(positions))
    ax.set_xticklabels(CLASSES)
    ax.set_ylabel("AP@0.5")
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="upper right")
    ax.set_title("AP@0.5 theo từng lớp trên test", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(IMG / "common/per_class_ap.png", bbox_inches="tight")
    plt.close(fig)


def plot_model_comparison() -> None:
    models = list(COMPARISON_METRICS)
    fig, axes = plt.subplots(1, 4, figsize=(11.4, 4.2), dpi=180)
    metric_titles = [
        ("mAP@0.5", "mAP@0.5"),
        ("mAP@0.5:0.95", "mAP@0.5:0.95"),
        ("AR/Recall", "AR/Recall"),
        ("FPS", "FPS"),
    ]

    for ax, (metric, title) in zip(axes, metric_titles):
        values = [COMPARISON_METRICS[m][metric] for m in models]
        bars = ax.bar(models, values, color=[MODEL_COLORS[m] for m in models], width=0.62)
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        if metric != "FPS":
            ax.set_ylim(0, 1.0)
        else:
            ax.set_ylim(0, 45)
        for bar, value in zip(bars, values):
            if metric == "FPS":
                label = f"{value:.1f}"
                label_y = bar.get_height() + 1.0
            else:
                label = f"{value:.2f}"
                label_y = bar.get_height() + 0.02
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                label_y,
                label,
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    fig.suptitle("Model comparison", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(IMG / "common/model_comparison.png", bbox_inches="tight")
    plt.close(fig)


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in ["DejaVuSans-Bold.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_labeled_box(draw: ImageDraw.ImageDraw, box: list[float], label: str, color: str, scale: float) -> None:
    x1, y1, x2, y2 = box
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    width = max(2, int(3 * scale))
    font = _load_font(max(9, int(12 * scale)))
    draw.rectangle([x1, y1, x2, y2], outline=rgb, width=width)

    label_bbox = draw.textbbox((0, 0), label, font=font)
    label_w = label_bbox[2] - label_bbox[0] + 6
    label_h = label_bbox[3] - label_bbox[1] + 4
    label_x = x1
    label_y = max(0, y1 - label_h)
    draw.rectangle([label_x, label_y, label_x + label_w, label_y + label_h], fill=rgb)
    draw.text((label_x + 3, label_y + 1), label, fill="white", font=font)


def _crop_gray_border(im: Image.Image) -> tuple[int, int, int, int]:
    arr = np.asarray(im)
    border_color = np.median(
        np.vstack([arr[:8].reshape(-1, 3), arr[-8:].reshape(-1, 3), arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3)]),
        axis=0,
    )
    gray_border = np.abs(arr.astype(int) - border_color.astype(int)).max(axis=2) < 8
    content = ~gray_border
    rows = np.where(content.any(axis=1))[0]
    cols = np.where(content.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return (0, 0, im.width, im.height)
    return (int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1)


def _build_fasterrcnn() -> torch.nn.Module:
    model = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, 4)
    model.load_state_dict(torch.load(ROOT / "faster-rcn/fasterrcnn_best.pth", map_location="cpu"))
    model.eval()
    return model


def _draw_fasterrcnn_prediction(image_path: Path, model: torch.nn.Module, conf: float) -> Image.Image:
    im = Image.open(image_path).convert("RGB")
    with torch.no_grad():
        pred = model([TF.to_tensor(im)])[0]

    draw = ImageDraw.Draw(im)
    color = (0, 255, 255)
    text_color = (20, 20, 80)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
    except OSError:
        font = ImageFont.load_default()

    for box, label, score in zip(pred["boxes"].cpu().numpy(), pred["labels"].cpu().numpy().astype(int), pred["scores"].cpu().numpy()):
        if float(score) < conf:
            continue
        x1, y1, x2, y2 = box.tolist()
        text = f"{FRCNN_NAMES.get(int(label), str(label))} {float(score):.2f}"
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        text_box = draw.textbbox((0, 0), text, font=font)
        text_w = text_box[2] - text_box[0] + 8
        text_h = text_box[3] - text_box[1] + 6
        label_y = max(0, y1 - text_h)
        draw.rectangle([x1, label_y, x1 + text_w, label_y + text_h], fill=color)
        draw.text((x1 + 4, label_y + 2), text, fill=text_color, font=font)
    return im


def _prepare_panel(im: Image.Image, title: str, *, max_w: int = 640, max_h: int = 420) -> Image.Image:
    crop = _crop_gray_border(im)
    im = im.crop(crop)
    scale = min(max_w / im.width, max_h / im.height)
    resized = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)

    title_h = 34
    panel = Image.new("RGB", (resized.width, resized.height + title_h), "white")
    draw = ImageDraw.Draw(panel)
    font = _load_font(20)
    text_box = draw.textbbox((0, 0), title, font=font)
    draw.text(((panel.width - (text_box[2] - text_box[0])) / 2, 4), title, fill="#222222", font=font)
    panel.paste(resized, (0, title_h))
    return panel


def _make_inference_sheet(image_path: Path, yolo: YOLO, rtdetr: RTDETR, fasterrcnn: torch.nn.Module) -> Image.Image:
    yolo_result = yolo.predict(str(image_path), imgsz=640, conf=0.35, iou=0.70, max_det=12, verbose=False)[0]
    rtdetr_result = rtdetr.predict(str(image_path), imgsz=640, conf=0.72, iou=0.70, max_det=12, verbose=False)[0]

    panels = [
        _prepare_panel(Image.fromarray(yolo_result.plot()[..., ::-1]), "YOLO"),
        _prepare_panel(_draw_fasterrcnn_prediction(image_path, fasterrcnn, conf=0.60), "Faster R-CNN"),
        _prepare_panel(Image.fromarray(rtdetr_result.plot()[..., ::-1]), "RT-DETR"),
    ]

    gap = 28
    panel_h = max(panel.height for panel in panels)
    panel_w = max(panel.width for panel in panels)
    width = panel_w * 2 + gap
    height = panel_h * 2 + gap
    canvas = Image.new("RGB", (width, height), "white")
    positions = [
        ((panel_w - panels[0].width) // 2, 0),
        (panel_w + gap + (panel_w - panels[1].width) // 2, 0),
        ((width - panels[2].width) // 2, panel_h + gap),
    ]
    for panel, (x, y) in zip(panels, positions):
        canvas.paste(panel, (x, y + (panel_h - panel.height) // 2))

    return canvas


def plot_inference_examples() -> None:
    yolo = YOLO(ROOT / "yolo/yolo/yolo_final/weights/best.pt")
    rtdetr = RTDETR(ROOT / "rtdetr_result/weights/rtdetr_best.pt")
    fasterrcnn = _build_fasterrcnn()

    first_sheet = None
    for idx, filename in enumerate(INFERENCE_IMAGES, start=1):
        sheet = _make_inference_sheet(ROOT / "data/images/test" / filename, yolo, rtdetr, fasterrcnn)
        sheet.save(IMG / f"common/inference_test_{idx}.png", quality=96)
        first_sheet = first_sheet or sheet

    if first_sheet is not None:
        first_sheet.save(IMG / "common/inference_correct_examples.png", quality=96)


def main() -> None:
    ensure_dirs()
    copy_existing_yolo_and_rtdetr_figures()
    plot_common_dataset()
    plot_yolo_curves()
    plot_fasterrcnn_figures()
    plot_model_comparison()
    plot_inference_examples()
    draw_arch(IMG / "yolo/architecture_summary.png", "YOLO Detection Pipeline", ["Input image\n640 x 640", "Backbone\nfeature extraction", "Neck\nmulti-scale fusion", "Detection head\nbox + class", "NMS\nfinal boxes"], "One-stage detector optimized for fast dense prediction.")
    draw_arch(IMG / "fasterrcnn/architecture_summary.png", "Faster R-CNN Detection Pipeline", ["Input image", "ResNet50-FPN\nbackbone", "Region Proposal\nNetwork", "RoI Align", "Box head\nclass + bbox"], "Two-stage detector: proposals followed by classification and box regression.")
    draw_arch(IMG / "rtdetr/architecture_summary_full.png", "RT-DETR Detection Pipeline", ["Input image\n640 x 640", "Backbone\nfeature extraction", "Hybrid encoder\nmulti-scale fusion", "Transformer decoder\nobject queries", "Detection head\nclass + bbox"], "End-to-end transformer-based detector.")


if __name__ == "__main__":
    main()
