#!/usr/bin/env python3
"""Build EURUSD market-state calibration report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_calibration import (
    build_market_state_calibration_report,
    render_market_state_calibration_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD market-state calibration report")
    parser.add_argument("--market-state-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_market_state_dataset.csv"))
    parser.add_argument("--market-state-report-json", type=Path, default=Path("tmp/validation-eurusd-market-state.json"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-market-state-calibration.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-market-state-calibration.md"))
    args = parser.parse_args()

    report = build_market_state_calibration_report(
        market_state_csv=args.market_state_csv,
        market_state_report_json=args.market_state_report_json,
        trial_approval_json=args.trial_approval_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_calibration_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
