#!/usr/bin/env python3
"""Standard-library entrypoint that exports entry.png into MAKEFUN_OUTPUT_DIR."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

DEFAULT_OUTPUT_DIR = "/output"
ENTRY_FILENAME = "entry.png"


def export_entry() -> Path:
    source = Path(__file__).resolve().parent / ENTRY_FILENAME
    if not source.is_file():
        raise FileNotFoundError(f"Expected rendered image at {source}")

    output_root = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    destination = output_root / ENTRY_FILENAME
    shutil.copyfile(source, destination)
    return destination


def main() -> int:
    try:
        written = export_entry()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Exported {written} ({written.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
