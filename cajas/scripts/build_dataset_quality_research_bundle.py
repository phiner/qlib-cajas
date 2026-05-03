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

from cajas.reports.dataset_quality_research import (  # noqa: E402
    build_dataset_quality_research_artifacts,
    render_dataset_quality_bundle_markdown,
)
from cajas.reports.runtime_io_summary import safe_json_write  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build dataset quality + chunked feature dry-run research bundle.")
    p.add_argument("--input-csv", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--label-col", action="append", dest="label_cols", default=[])
    p.add_argument("--feature-col", action="append", dest="feature_cols", default=[])
    p.add_argument("--datetime-col", default="datetime")
    p.add_argument("--instrument-col", default="instrument")
    p.add_argument("--chunk-size", type=int, default=50000)
    p.add_argument("--row-limit", type=int, default=None)
    p.add_argument("--imbalance-warn-threshold", type=float, default=0.75)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    bundle = build_dataset_quality_research_artifacts(
        input_csv=args.input_csv,
        label_columns=args.label_cols,
        feature_columns=args.feature_cols,
        datetime_col=args.datetime_col,
        instrument_col=args.instrument_col,
        chunk_size=args.chunk_size,
        row_limit=args.row_limit,
        imbalance_warn_threshold=args.imbalance_warn_threshold,
    )
    elapsed = max(0.0, time.perf_counter() - t0)
    rows = bundle["dataset_quality_report"]["row_count"]
    rps = round(rows / elapsed, 3) if elapsed > 0 else None
    bundle["dataset_quality_report"]["chunked_feature_dry_run"]["rows_per_second"] = rps
    bundle["dataset_quality_report"]["chunked_feature_dry_run"]["elapsed_seconds"] = round(elapsed, 3)

    md = render_dataset_quality_bundle_markdown(bundle=bundle)
    safe_json_write(out / "dataset_quality_report.json", bundle["dataset_quality_report"])
    safe_json_write(out / "feature_schema_manifest.json", bundle["feature_schema_manifest"])
    safe_json_write(out / "offline_research_queue_summary.json", bundle["offline_research_queue_summary"])
    (out / "dataset_quality_report.md").write_text(md["dataset_quality_report_md"], encoding="utf-8")
    (out / "feature_schema_manifest.md").write_text(md["feature_schema_manifest_md"], encoding="utf-8")
    (out / "offline_research_queue_summary.md").write_text(md["offline_research_queue_summary_md"], encoding="utf-8")

    if args.json:
        print(json.dumps({"output_dir": str(out), "row_count": rows, "rows_per_second": rps}, ensure_ascii=True, indent=2))
    else:
        print("Dataset quality research bundle completed.")
        print(f"output dir: {out}")
        print(f"row_count: {rows}")
        print(f"rows_per_second: {rps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
