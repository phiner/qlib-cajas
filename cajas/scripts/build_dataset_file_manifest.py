#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.data_io.dataset_file_manifest import build_dataset_file_manifest
from cajas.reports.runtime_io_summary import safe_json_write


def main() -> int:
    p = argparse.ArgumentParser(description="Build dataset file manifest from CSV metadata.")
    p.add_argument("--data-root", required=True)
    p.add_argument("--pattern", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--include-hash", action="store_true")
    p.add_argument("--count-rows", action="store_true")
    args = p.parse_args()

    report = build_dataset_file_manifest(
        data_root=args.data_root,
        pattern=args.pattern,
        include_hash=args.include_hash,
        count_rows=args.count_rows,
    )
    safe_json_write(args.out, report)
    print(f"output: {args.out}")
    print(f"source_files: {len(report['source_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
