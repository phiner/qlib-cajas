#!/usr/bin/env python3
"""Build EURUSD micro-pattern rule candidates report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_rule_candidates import (
    build_micro_pattern_rule_candidates_report,
    render_micro_pattern_rule_candidates_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD micro-pattern rule candidates report")
    parser.add_argument("--manual-labels-json", type=Path, required=True)
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument(
        "--completed-labels-csv",
        type=Path,
        default=Path("tmp/eurusd/EURUSD_15m_micro_pattern_review_packet_completed_template.csv"),
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_micro_pattern_rule_candidates_report(
        args.manual_labels_json,
        args.trial_approval_json,
        args.completed_labels_csv,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_micro_pattern_rule_candidates_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
