"""CLI entry point – same pipeline the Kaggle notebook runs."""

from __future__ import annotations

import argparse
import sys

import config
from crawler import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Crawl YouTube traffic videos, extract frames, detect no-helmet scenes via Ollama LLaVA.",
    )
    p.add_argument(
        "--skip-download",
        action="store_true",
        help="Do not download from YouTube; use --video paths only.",
    )
    p.add_argument(
        "--video",
        action="append",
        dest="videos",
        default=None,
        metavar="PATH",
        help="Local video file (repeatable). Implies you use --skip-download.",
    )
    p.add_argument(
        "--max-videos",
        type=int,
        default=None,
        metavar="N",
        help="Cap total downloaded videos (default: config.MAX_VIDEOS_TOTAL).",
    )
    p.add_argument(
        "--max-per-query",
        type=int,
        default=None,
        metavar="N",
        help="Max videos per search query (default: config.MAX_VIDEOS_PER_QUERY).",
    )
    p.add_argument(
        "--max-duration",
        type=int,
        default=None,
        metavar="SEC",
        help="Skip videos longer than this many seconds (default: config).",
    )
    p.add_argument(
        "--frame-interval",
        type=float,
        default=None,
        metavar="SEC",
        help="Seconds between extracted frames (default: config.FRAME_INTERVAL).",
    )
    p.add_argument(
        "--model",
        default=None,
        metavar="NAME",
        help="Ollama vision model (default: config.OLLAMA_MODEL).",
    )
    p.add_argument(
        "--ollama-host",
        default=None,
        metavar="URL",
        help="Ollama server URL (default: OLLAMA_HOST env or http://localhost:11434).",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory for saved violation frames (default: config.OUTPUT_DIR).",
    )
    p.add_argument(
        "--results-csv",
        default=None,
        metavar="PATH",
        help="Path for results CSV (default: config.RESULTS_CSV).",
    )
    p.add_argument(
        "--query",
        "-q",
        action="append",
        dest="queries",
        default=None,
        metavar="TEXT",
        help=(
            "YouTube search string. Repeat to set the full query list; replaces "
            "config.SEARCH_QUERIES when at least one is given."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.ollama_host:
        config.OLLAMA_HOST = args.ollama_host

    if args.skip_download:
        if not args.videos:
            print("error: --skip-download requires at least one --video PATH", file=sys.stderr)
            return 2
    elif args.videos:
        print(
            "warning: --video is ignored without --skip-download (downloading from YouTube).",
            file=sys.stderr,
        )

    queries = args.queries if args.queries else None

    df = run_pipeline(
        queries=queries,
        skip_download=args.skip_download,
        video_paths=args.videos,
        max_per_query=args.max_per_query,
        max_total=args.max_videos,
        max_duration=args.max_duration,
        frame_interval=args.frame_interval,
        output_dir=args.output_dir,
        results_csv=args.results_csv,
        ollama_model=args.model,
    )
    if df.empty:
        print("No violations detected.")
    else:
        csv_path = args.results_csv or config.RESULTS_CSV
        print(f"\n{len(df)} violation frame(s) saved. See {csv_path}")
    return 0


def run_cli() -> None:
    """Entry point for the ``helmet-crawl`` console script."""
    raise SystemExit(main())


if __name__ == "__main__":
    run_cli()
