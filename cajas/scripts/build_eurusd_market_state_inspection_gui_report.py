#!/usr/bin/env python3
"""Build EURUSD market-state inspection GUI readiness report artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_inspection_gui import (
    build_market_state_inspection_gui_report,
    render_market_state_inspection_gui_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD market-state inspection GUI readiness report")
    parser.add_argument("--inspection-packet-csv", type=Path, required=True)
    parser.add_argument("--raw-csv", type=Path, required=True)
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_market_state_inspection_gui_report(
        inspection_packet_csv=args.inspection_packet_csv,
        raw_csv=args.raw_csv,
        trial_approval_json=args.trial_approval_json,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_inspection_gui_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

