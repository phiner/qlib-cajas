#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.dataset_quality_research import build_chunked_feature_dry_run, render_chunked_feature_dry_run_markdown  # noqa: E402
from cajas.reports.runtime_io_summary import safe_json_write  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run chunked feature dry-run diagnostics (offline research only).")
    p.add_argument("--input", required=True)
    p.add_argument("--labels", action="append", default=[])
    p.add_argument("--feature-col", action="append", default=[])
    p.add_argument("--datetime-col", default="datetime")
    p.add_argument("--instrument-col", default="instrument")
    p.add_argument("--row-limit", type=int, default=10000)
    p.add_argument("--chunk-size", type=int, default=5000)
    p.add_argument("--sample-only", action="store_true")
    p.add_argument("--allow-large-data", action="store_true")
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args(argv)

    row_limit = args.row_limit
    if args.sample_only and (row_limit is None or row_limit > 10000):
        row_limit = 10000
    if not args.allow_large_data and row_limit is None:
        print("error: row_limit required unless --allow-large-data is set", file=sys.stderr)
        return 2

    start = time.perf_counter()
    report = build_chunked_feature_dry_run(
        input_csv=args.input,
        label_columns=args.labels,
        feature_columns=args.feature_col,
        datetime_col=args.datetime_col,
        instrument_col=args.instrument_col,
        chunk_size=args.chunk_size,
        row_limit=row_limit,
    )
    elapsed = max(0.0, time.perf_counter() - start)
    node = report["chunked_feature_dry_run"]
    row_count = node.get("row_count", 0)
    node["elapsed_seconds"] = round(elapsed, 3)
    node["rows_per_second"] = round(row_count / elapsed, 3) if elapsed > 0 else None

    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    safe_json_write(out_json, report)
    out_md.write_text(render_chunked_feature_dry_run_markdown(dry_run=report), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(out_json), "out_md": str(out_md), "row_count": row_count}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
