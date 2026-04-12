#!/usr/bin/env python3
"""Create timestamped source snapshots and keep only N recent backups.

By default, excludes runtime data, databases, secrets, and sample confidential datasets.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "logs",
    ".runtime",
}

EXCLUDED_PATHS = {
    "data/db",
    "data/backups",
    "Context/Sample",
    "backend/sample_data",
}

EXCLUDED_PATTERNS = [
    "*.db",
    "*.log",
    "*.pyc",
    "*.pyo",
    ".env",
    "backend/.env",
]


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()

    parts = rel.split("/")
    if any(part in EXCLUDED_DIRS for part in parts):
        return True

    for excluded in EXCLUDED_PATHS:
        if rel == excluded or rel.startswith(excluded + "/"):
            return True

    return any(fnmatch.fnmatch(rel, pattern) for pattern in EXCLUDED_PATTERNS)


def create_snapshot(root: Path, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = output_dir / f"siem-v2-src-{timestamp}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zf:
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if should_skip(path, root):
                continue
            rel = path.relative_to(root)
            zf.write(path, arcname=rel.as_posix())

    return archive


def rotate(output_dir: Path, keep: int) -> None:
    files = sorted(output_dir.glob("siem-v2-src-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        old.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and rotate SIEM V2 source backups")
    parser.add_argument("--output-dir", default="data/backups/repo_snapshots", help="Directory for zip snapshots")
    parser.add_argument("--keep", type=int, default=14, help="Number of snapshots to keep")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    root = script_path.parent.parent
    output_dir = (root / args.output_dir).resolve()

    archive = create_snapshot(root, output_dir)
    rotate(output_dir, max(1, args.keep))

    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"Snapshot created: {archive}")
    print(f"Size: {size_mb:.2f} MB")
    print(f"Retention: keep last {max(1, args.keep)} snapshot(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
