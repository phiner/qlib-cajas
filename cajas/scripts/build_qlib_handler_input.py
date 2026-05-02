#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_handler_input_builder import build_qlib_handler_input


def main() -> int:
    p = argparse.ArgumentParser(description="Build offline handler input package from a feature/label CSV.")
    p.add_argument("--input-csv", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--instrument-col", default="instrument")
    p.add_argument("--datetime-col", default="datetime")
    p.add_argument("--label-col", action="append", dest="label_cols")
    p.add_argument("--no-sort", action="store_true")
    p.add_argument("--row-limit", type=int, default=None)
    p.add_argument("--chunk-size", type=int, default=None)
    p.add_argument("--sample-only", action="store_true")
    p.add_argument("--allow-large-data", action="store_true")
    args = p.parse_args()

    manifest = build_qlib_handler_input(
        input_csv=args.input_csv,
        out_dir=args.out_dir,
        instrument_col=args.instrument_col,
        datetime_col=args.datetime_col,
        label_columns=args.label_cols,
        sort_rows=not args.no_sort,
        row_limit=args.row_limit,
        chunk_size=args.chunk_size,
        sample_only=args.sample_only,
        allow_large_data=args.allow_large_data,
    )
    print("Qlib handler input build completed.")
    print(f"output dir: {Path(args.out_dir).expanduser().resolve()}")
    print(f"status: {manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
