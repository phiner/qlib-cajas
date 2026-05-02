#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.data_io.large_csv_metadata import inspect_large_csv_metadata
from cajas.reports.runtime_io_summary import safe_json_write


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect large CSV metadata with cheap defaults.")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--sample-lines", type=int, default=100)
    p.add_argument("--count-rows", action="store_true")
    p.add_argument("--hash", action="store_true")
    p.add_argument("--chunk-size", type=int, default=100000)
    args = p.parse_args()

    report = inspect_large_csv_metadata(
        input_path=args.input,
        sample_lines=args.sample_lines,
        count_rows=args.count_rows,
        compute_hash=args.hash,
        chunk_size=args.chunk_size,
    )
    safe_json_write(args.out, report)
    print(f"output: {args.out}")
    print(f"size_bytes: {report['size_bytes']}")
    print(f"row_count_mode: {report['row_count_mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
