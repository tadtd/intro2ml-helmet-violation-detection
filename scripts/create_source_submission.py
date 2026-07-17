"""Create a source-code submission archive.

The archive intentionally excludes local environments, caches, secrets, model
weights, report/slide artifacts, and generated files. It also writes a small
MODEL_WEIGHTS_LINKS.md file into the archive so reviewers know where to
download the trained model artifacts.

Examples:
    python scripts/create_source_submission.py
    python scripts/create_source_submission.py --dry-run
    python scripts/create_source_submission.py --output submission/source.zip
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path


DEFAULT_ARCHIVE_NAME = "helmet-violation-source.zip"
MODEL_URL_RE = re.compile(r"https?://[^\s)\]>,]+")

EXCLUDED_DIR_NAMES = {
    ".agents",
    ".cache",
    ".git",
    ".ipynb_checkpoints",
    ".kube",
    ".mypy_cache",
    ".next",
    ".nox",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "env.bak",
    "ENV",
    "htmlcov",
    "node_modules",
    "venv",
    "venv.bak",
}

MODEL_WEIGHT_EXTENSIONS = {
    ".ckpt",
    ".engine",
    ".h5",
    ".onnx",
    ".pb",
    ".pt",
    ".pth",
    ".safetensors",
    ".tflite",
    ".weights",
}

DEMO_MEDIA_EXTENSIONS = {
    ".avi",
    ".mkv",
    ".mov",
    ".mp4",
    ".webm",
}

GENERATED_FILE_PATTERNS = {
    "*.bak",
    "*.log",
    "*.pyc",
    "*.pyd",
    "*.pyo",
    "*.swp",
    "*.temp",
    "*.tmp",
    ".DS_Store",
    "Thumbs.db",
}

SECRET_FILE_PATTERNS = {
    "*.crt",
    "*.key",
    "*.pem",
    "*.secret.yaml",
    ".env",
    ".env.*",
    "github-key.json",
    "kubeconfig*",
}

MODEL_URL_FILES = [
    "backend/inference/weights/README.md",
    "models/checkpoints/README.md",
    "models/README.md",
    "README.md",
]


def as_posix_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def matches_any(name: str, patterns: set[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def directory_exclusion_reason(relative_path: str, dirname: str) -> str | None:
    if dirname in EXCLUDED_DIR_NAMES:
        return f"generated/local directory: {dirname}"

    if relative_path == "report" or relative_path.startswith("report/"):
        return "report artifact"

    if relative_path == "slide" or relative_path.startswith("slide/"):
        return "slide artifact"

    generated_dirs = (
        "submission",
        "deploy/release-state",
        "deploy/.scratch",
        "supabase/.temp",
    )
    if relative_path in generated_dirs or any(
        relative_path.startswith(f"{item}/") for item in generated_dirs
    ):
        return "generated output directory"

    parts = relative_path.split("/")
    if len(parts) >= 2 and parts[0] == "data":
        return "dataset directory under data"

    if "downloads" in parts or "output" in parts:
        return "download/output artifact directory"

    return None


def file_exclusion_reason(
    path: Path,
    relative_path: str,
    output_path: Path,
    include_demo_media: bool,
) -> str | None:
    filename = path.name
    suffix = path.suffix.lower()
    parts = relative_path.split("/")

    if path.resolve() == output_path.resolve():
        return "output archive"

    if ".env.example" == filename:
        return None

    for part in parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return f"generated/local directory: {part}"

    if relative_path == "report" or relative_path.startswith("report/"):
        return "report artifact"

    if relative_path == "slide" or relative_path.startswith("slide/"):
        return "slide artifact"

    if len(parts) >= 2 and parts[0] == "data":
        return "dataset directory under data"

    if "downloads" in parts or "output" in parts:
        return "download/output artifact directory"

    if matches_any(filename, SECRET_FILE_PATTERNS):
        return "secret/local config file"

    if suffix in MODEL_WEIGHT_EXTENSIONS:
        return "model weight file"

    if not include_demo_media and suffix in DEMO_MEDIA_EXTENSIONS:
        return "demo/media file"

    if matches_any(filename, GENERATED_FILE_PATTERNS):
        return "generated/cache file"

    return None


def discover_model_urls(root: Path, explicit_url: str | None) -> list[str]:
    urls: list[str] = []

    for relative_file in MODEL_URL_FILES:
        path = root / relative_file
        if not path.is_file():
            continue

        content = path.read_text(encoding="utf-8", errors="replace")
        for match in MODEL_URL_RE.findall(content):
            url = match.rstrip(".,;")
            if any(
                domain in url
                for domain in (
                    "huggingface.co",
                    "drive.google.com",
                    "kaggle.com",
                    "zenodo.org",
                )
            ):
                if url not in urls:
                    urls.append(url)

    if explicit_url and explicit_url not in urls:
        urls.append(explicit_url)

    return urls


def scan_files(
    root: Path,
    output_path: Path,
    include_demo_media: bool,
) -> tuple[list[tuple[Path, str]], list[tuple[str, str, int]], list[tuple[str, str]]]:
    included: list[tuple[Path, str]] = []
    excluded_files: list[tuple[str, str, int]] = []
    skipped_dirs: list[tuple[str, str]] = []

    for current_root, dirs, files in os.walk(root, topdown=True):
        current = Path(current_root)

        kept_dirs: list[str] = []
        for dirname in dirs:
            child = current / dirname
            relative = as_posix_relative(child, root)
            reason = directory_exclusion_reason(relative, dirname)
            if reason is None:
                kept_dirs.append(dirname)
            else:
                skipped_dirs.append((relative, reason))
        dirs[:] = kept_dirs

        for filename in files:
            path = current / filename
            relative = as_posix_relative(path, root)
            reason = file_exclusion_reason(
                path=path,
                relative_path=relative,
                output_path=output_path,
                include_demo_media=include_demo_media,
            )
            try:
                size = path.stat().st_size
            except OSError:
                size = 0

            if reason is None:
                included.append((path, relative))
            else:
                excluded_files.append((relative, reason, size))

    return included, excluded_files, skipped_dirs


def write_model_links(stage_root: Path, model_urls: list[str]) -> None:
    lines = [
        "# Model Weights",
        "",
        "Model weight files are intentionally excluded from this source-code submission.",
        "Download the trained model artifacts from:",
        "",
        *[f"- {url}" for url in model_urls],
        "",
        "Expected inference weight filenames:",
        "",
        "- backend/inference/weights/yolo_best.onnx",
        "- backend/inference/weights/rtdetr_best.onnx",
        "- backend/inference/weights/fasterrcnn_best.onnx",
        "",
        "Expected training checkpoint filenames, if retraining/evaluation is needed:",
        "",
        "- models/checkpoints/yolo_best.pt",
        "- models/checkpoints/rtdetr_best.pt",
        "- models/checkpoints/fasterrcnn_best.pth",
        "",
    ]
    (stage_root / "MODEL_WEIGHTS_LINKS.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_manifest(
    stage_root: Path,
    included: list[tuple[Path, str]],
    excluded_files: list[tuple[str, str, int]],
    skipped_dirs: list[tuple[str, str]],
) -> None:
    lines = [
        "Source submission manifest",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Included files: {len(included)}",
        f"Excluded files: {len(excluded_files)}",
        f"Skipped directories: {len(skipped_dirs)}",
        "",
        "Excluded groups:",
    ]

    skipped_counter = Counter(reason for _, reason in skipped_dirs)
    excluded_counter = Counter(reason for _, reason, _ in excluded_files)
    for reason, count in (skipped_counter + excluded_counter).most_common():
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "Included paths:"])
    lines.extend(relative for _, relative in sorted(included, key=lambda item: item[1]))
    lines.append("")

    (stage_root / "SUBMISSION_MANIFEST.txt").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def create_archive(
    root: Path,
    output_path: Path,
    included: list[tuple[Path, str]],
    model_urls: list[str],
    excluded_files: list[tuple[str, str, int]],
    skipped_dirs: list[tuple[str, str]],
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="helmet-submission-") as tmpdir:
        stage_root = Path(tmpdir) / "helmet-violation-detection"
        stage_root.mkdir(parents=True)

        for source, relative in included:
            target = stage_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        write_model_links(stage_root, model_urls)
        write_manifest(stage_root, included, excluded_files, skipped_dirs)

        if output_path.exists():
            output_path.unlink()

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in stage_root.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(stage_root).as_posix())

    return output_path.stat().st_size


def print_summary(
    root: Path,
    output_path: Path,
    included: list[tuple[Path, str]],
    excluded_files: list[tuple[str, str, int]],
    skipped_dirs: list[tuple[str, str]],
    model_urls: list[str],
) -> None:
    included_bytes = sum(path.stat().st_size for path, _ in included)
    excluded_bytes = sum(size for _, _, size in excluded_files)

    print(f"Repository: {root}")
    print(f"Output: {output_path}")
    print(f"Included files: {len(included)} ({included_bytes / 1024 / 1024:.2f} MB)")
    print(f"Excluded files: {len(excluded_files)} ({excluded_bytes / 1024 / 1024:.2f} MB)")
    print(f"Skipped directories: {len(skipped_dirs)}")
    print()
    print("Model download link(s):")
    for url in model_urls:
        print(f"  - {url}")

    skipped_counter = Counter(reason for _, reason in skipped_dirs)
    excluded_counter = Counter(reason for _, reason, _ in excluded_files)
    print()
    print("Top exclusion groups:")
    for reason, count in (skipped_counter + excluded_counter).most_common(20):
        print(f"  - {reason}: {count}")


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_output = repo_root / "submission" / DEFAULT_ARCHIVE_NAME

    parser = argparse.ArgumentParser(
        description="Create a source-code submission zip archive."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=repo_root,
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help=f"Output zip path. Defaults to {default_output}.",
    )
    parser.add_argument(
        "--model-url",
        default=None,
        help="Extra model download URL to include if it is not already in README files.",
    )
    parser.add_argument(
        "--include-demo-media",
        action="store_true",
        help="Include demo videos/media files. By default they are excluded.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be included/excluded; do not create a zip.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output_path = args.output.resolve()

    if not root.is_dir():
        print(f"Repository root does not exist: {root}", file=sys.stderr)
        return 2

    model_urls = discover_model_urls(root, args.model_url)
    if not model_urls:
        print(
            "No model download URL was found. Add one to a model README or pass "
            "--model-url <url>.",
            file=sys.stderr,
        )
        return 2

    included, excluded_files, skipped_dirs = scan_files(
        root=root,
        output_path=output_path,
        include_demo_media=args.include_demo_media,
    )

    print_summary(
        root=root,
        output_path=output_path,
        included=included,
        excluded_files=excluded_files,
        skipped_dirs=skipped_dirs,
        model_urls=model_urls,
    )

    if args.dry_run:
        print()
        print("Dry run only. No archive was created.")
        return 0

    archive_size = create_archive(
        root=root,
        output_path=output_path,
        included=included,
        model_urls=model_urls,
        excluded_files=excluded_files,
        skipped_dirs=skipped_dirs,
    )
    print()
    print(f"Created archive: {output_path}")
    print(f"Archive size: {archive_size / 1024 / 1024:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
