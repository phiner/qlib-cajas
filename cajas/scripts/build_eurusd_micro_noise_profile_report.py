#!/usr/bin/env python3
"""Build EURUSD micro-noise profile report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_noise_profile import (
    build_micro_noise_profile_report,
    render_micro_noise_profile_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD micro-noise profile report")
    parser.add_argument("--market-state-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_market_state_dataset.csv"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-micro-noise-profile.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-micro-noise-profile.md"))
    args = parser.parse_args()

    report = build_micro_noise_profile_report(
        market_state_csv=args.market_state_csv,
        trial_approval_json=args.trial_approval_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_micro_noise_profile_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
