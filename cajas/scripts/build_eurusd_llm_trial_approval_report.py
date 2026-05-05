#!/usr/bin/env python3
"""Build explicit approval and minimal real LLM trial boundary report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_llm_trial_approval import (
    build_llm_trial_approval_report,
    render_llm_trial_approval_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD LLM trial approval report")
    parser.add_argument("--readiness-json", type=Path, required=True)
    parser.add_argument("--approval-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.md"))
    args = parser.parse_args()

    report = build_llm_trial_approval_report(
        readiness_json=args.readiness_json,
        approval_json=args.approval_json,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_llm_trial_approval_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "approval_status": report.get("status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
