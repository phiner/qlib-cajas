#!/usr/bin/env python3
"""Build EURUSD market-state inspection feedback report artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_inspection_feedback import (
    build_market_state_inspection_feedback_report,
    render_market_state_inspection_feedback_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD market-state inspection feedback report")
    parser.add_argument("--inspection-packet-csv", type=Path, required=True)
    parser.add_argument("--completed-feedback-csv", type=Path, required=True)
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_market_state_inspection_feedback_report(
        inspection_packet_csv=args.inspection_packet_csv,
        completed_feedback_csv=args.completed_feedback_csv,
        trial_approval_json=args.trial_approval_json,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_inspection_feedback_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
