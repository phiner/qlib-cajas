#!/usr/bin/env python3
"""Build EURUSD clean dataset view report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_clean_dataset_view import (
    build_validation_eurusd_clean_dataset_view,
    render_validation_eurusd_clean_dataset_view_markdown,
)


def _parse_inputs(raw: list[str]) -> list[Path]:
    out: list[Path] = []
    for token in raw:
        for p in token.split(","):
            v = p.strip()
            if v:
                out.append(Path(v))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD clean dataset view report")
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--anomaly-triage-report", required=True, type=Path)
    parser.add_argument("--output-clean-csv", required=True, type=Path)
    parser.add_argument("--output-quarantine-csv", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--min-rows", default=20, type=int)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_clean_dataset_view(
        input_paths=_parse_inputs(args.input),
        anomaly_triage_report=args.anomaly_triage_report,
        output_clean_csv=args.output_clean_csv,
        output_quarantine_csv=args.output_quarantine_csv,
        min_rows=args.min_rows,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_clean_dataset_view_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
