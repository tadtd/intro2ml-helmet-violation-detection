from __future__ import annotations

from pathlib import Path
import csv

import matplotlib.pyplot as plt
import numpy as np


def write_learning_curves_csv(history: list[dict], out_path: Path) -> None:
    fieldnames = ["epoch", "train_loss", "val_loss", "lr"]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in history:
            writer.writerow({key: row.get(key) for key in fieldnames})


def plot_learning_curves(history: list[dict], out_path: Path) -> None:
    epochs = [row["epoch"] for row in history]
    train_loss = [row["train_loss"] for row in history]
    val_loss = [row["val_loss"] for row in history]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, train_loss, marker="o", label="Train loss")
    ax.plot(epochs, val_loss, marker="o", label="Validation loss")
    ax.set_title("Learning Curves")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def write_confusion_matrix_csv(matrix: np.ndarray, labels: list[str], out_path: Path) -> None:
    display_labels = labels + ["background"]
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ground_truth/predicted", *display_labels])
        for label, row in zip(display_labels, matrix.tolist()):
            writer.writerow([label, *row])


def plot_confusion_matrix(matrix: np.ndarray, labels: list[str], out_path: Path) -> None:
    display_labels = labels + ["background"]
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(display_labels)))
    ax.set_yticks(range(len(display_labels)))
    ax.set_xticklabels(display_labels, rotation=35, ha="right")
    ax.set_yticklabels(display_labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground truth")
    ax.set_title("Confusion Matrix")

    threshold = matrix.max() / 2 if matrix.size and matrix.max() else 0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = int(matrix[i, j])
            color = "white" if value > threshold else "black"
            ax.text(j, i, str(value), ha="center", va="center", color=color, fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def learning_curve_comment(history: list[dict]) -> str:
    if len(history) < 2:
        return "There is not enough data to assess the learning curve trend."

    first = history[0]
    last = history[-1]
    train_delta = first["train_loss"] - last["train_loss"]
    val_delta = first["val_loss"] - last["val_loss"]
    gap = last["val_loss"] - last["train_loss"]

    comments = []
    if train_delta > 0 and val_delta > 0:
        comments.append("Both train loss and validation loss decrease, so the model shows convergence.")
    elif train_delta > 0 and val_delta <= 0:
        comments.append("Train loss decreases but validation loss does not improve, which may indicate overfitting.")
    else:
        comments.append("Loss does not decrease clearly, so more epochs or learning-rate tuning may be needed.")

    if gap > 0.2 * max(last["train_loss"], 1e-8):
        comments.append("The validation/train loss gap is still large, suggesting possible overfitting.")
    else:
        comments.append("The validation/train loss gap is not too large.")

    return " ".join(comments)
