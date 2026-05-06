#!/usr/bin/env python3
"""Build market-state Qlib adapter contract report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_market_state_qlib_adapter_contract import (
    build_market_state_qlib_adapter_contract_report,
    render_market_state_qlib_adapter_contract_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD market-state qlib adapter contract report")
    parser.add_argument("--market-state-csv", type=Path, required=True)
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_market_state_qlib_adapter_contract_report(args.market_state_csv, args.trial_approval_json)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_market_state_qlib_adapter_contract_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
