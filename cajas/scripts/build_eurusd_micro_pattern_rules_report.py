#!/usr/bin/env python3
"""Build externalized EURUSD micro-pattern rules validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_rules import (
    build_micro_pattern_rules_report,
    render_micro_pattern_rules_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD micro-pattern rules report")
    parser.add_argument("--rules-json", type=Path, default=Path("cajas/data_examples/eurusd_micro_pattern_rules_v0.json"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-micro-pattern-rules.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-micro-pattern-rules.md"))
    args = parser.parse_args()

    report = build_micro_pattern_rules_report(args.rules_json, args.trial_approval_json)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_micro_pattern_rules_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
