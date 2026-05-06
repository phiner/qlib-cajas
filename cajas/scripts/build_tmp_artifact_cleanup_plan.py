#!/usr/bin/env python3
"""Build conservative tmp artifact cleanup plan (dry-run)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_tmp_artifact_cleanup_plan import (
    build_tmp_artifact_cleanup_plan,
    render_tmp_artifact_cleanup_plan_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build tmp artifact cleanup plan")
    parser.add_argument("--tmp-root", type=Path, default=Path("tmp"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_tmp_artifact_cleanup_plan(args.tmp_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_tmp_artifact_cleanup_plan_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
