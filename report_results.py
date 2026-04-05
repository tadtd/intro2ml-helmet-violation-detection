"""Summarize helmet crawl results and write a grid image (CLI + importable helpers)."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

import config


def load_results(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()


def print_summary(df: pd.DataFrame, csv_path: str) -> None:
    if df.empty:
        print("No violations detected.")
        return
    print(f"Total violation frames: {len(df)}")
    print("\nViolations per video:")
    print(df.groupby("video_id")["violation_count"].sum().sort_values(ascending=False))
    print(f"\nResults CSV: {csv_path}")
    print("\nFirst rows:")
    print(df.head(10).to_string())


def save_violations_grid(
    df: pd.DataFrame,
    grid_path: Path,
    *,
    max_samples: int = 16,
) -> None:
    if df.empty:
        print("No violation frames; skipping grid image.")
        return
    sample = df.head(max_samples)
    n = len(sample)
    cols = 4
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4 * rows))
    axes_list = axes.flatten() if n > 1 else [axes]
    last_i = -1
    for last_i, (_, row) in enumerate(sample.iterrows()):
        img = Image.open(row["frame_path"])
        axes_list[last_i].imshow(img)
        axes_list[last_i].set_title(
            f"{row['video_id']}\n{row['timestamp_s']}s — {row['violation_count']} violation(s)",
            fontsize=9,
        )
        axes_list[last_i].axis("off")
    for j in range(last_i + 1, len(axes_list)):
        axes_list[j].axis("off")
    plt.suptitle("No-Helmet Violations Detected", fontsize=14, y=1.01)
    plt.tight_layout()
    grid_path = Path(grid_path)
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(grid_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved grid image: {grid_path}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Print crawl summary from results CSV and save violations_grid.png.",
    )
    p.add_argument(
        "--csv",
        default=None,
        metavar="PATH",
        help="Results CSV (default: config.RESULTS_CSV).",
    )
    p.add_argument(
        "--grid",
        default=None,
        metavar="PATH",
        help="Output PNG (default: parent of OUTPUT_DIR / violations_grid.png).",
    )
    p.add_argument(
        "--max-samples",
        type=int,
        default=16,
        metavar="N",
        help="Max frames in the grid image.",
    )
    args = p.parse_args(argv)

    csv_path = args.csv or config.RESULTS_CSV
    if args.grid:
        grid_path = Path(args.grid)
    else:
        grid_path = Path(config.OUTPUT_DIR).parent / "violations_grid.png"

    df = load_results(csv_path)
    print_summary(df, csv_path)
    save_violations_grid(df, grid_path, max_samples=args.max_samples)
    return 0


def run_cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    run_cli()
