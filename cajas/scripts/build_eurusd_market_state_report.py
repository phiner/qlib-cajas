#!/usr/bin/env python3
"""Build EURUSD market-state dataset/report artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state import (
    build_market_state_report,
    render_market_state_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD 3/8/24/128 market-state prototype artifacts")
    parser.add_argument("--input-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_market_state_dataset.csv"))
    parser.add_argument("--output-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_market_state_dataset.jsonl"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-market-state.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-market-state.md"))
    args = parser.parse_args()

    report = build_market_state_report(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        output_jsonl=args.output_jsonl,
        trial_approval_json=args.trial_approval_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
