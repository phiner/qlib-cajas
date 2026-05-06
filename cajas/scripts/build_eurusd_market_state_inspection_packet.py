#!/usr/bin/env python3
"""Build EURUSD four-layer inspection packet artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_inspection_packet import (
    build_market_state_inspection_packet,
    render_market_state_inspection_packet_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD four-layer market-state inspection packet")
    parser.add_argument("--sample-export-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--max-rows", type=int, default=40)
    args = parser.parse_args()

    report = build_market_state_inspection_packet(
        sample_export_csv=args.sample_export_csv,
        output_csv=args.output_csv,
        output_jsonl=args.output_jsonl,
        trial_approval_json=args.trial_approval_json,
        max_rows=args.max_rows,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_inspection_packet_markdown(report, args.output_csv), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
