#!/usr/bin/env python3
"""Entrypoint for make.fun news-image-20261125 (Wednesday 25 November 2026).

Copies the pre-rendered deterministic 1024x1024 PNG front page (`entry.png`
located alongside this script) into the directory specified by
`MAKEFUN_OUTPUT_DIR` (default `/output`), creating parent directories if needed.
Uses only the Python standard library (Python 3.13 compatible).
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def export_entry() -> Path:
    """Copy the rendered `entry.png` to the configured make.fun output path."""
    src = Path(__file__).resolve().parent / "entry.png"
    if not src.is_file():
        raise FileNotFoundError(f"Rendered front page not found: {src}")

    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dest = Path(output_dir) / "entry.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    return dest


def main() -> int:
    try:
        export_entry()
    except OSError as exc:
        print(f"Error copying entry image: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
