#!/usr/bin/env python3
"""Build runtime edge risk report from timing + runtime budget artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_runtime_edge import (
    build_validation_runtime_edge_report,
    render_validation_runtime_edge_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation runtime edge report")
    parser.add_argument("--timing-json", required=True, type=Path, help="Fast validation timing JSON")
    parser.add_argument("--runtime-budget-report", required=True, type=Path, help="Runtime budget report JSON")
    parser.add_argument("--out-json", required=True, type=Path, help="Output JSON path")
    parser.add_argument("--out-md", required=True, type=Path, help="Output markdown path")
    parser.add_argument("--watch-threshold-ratio", type=float, default=0.15, help="Watch threshold ratio")
    args = parser.parse_args(argv)

    payload = build_validation_runtime_edge_report(
        timing_json_path=args.timing_json,
        runtime_budget_report_path=args.runtime_budget_report,
        watch_threshold_ratio=args.watch_threshold_ratio,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_runtime_edge_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
