#!/usr/bin/env python3
"""Run fail-closed EURUSD LLM second-review trial skeleton."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.research.eurusd_llm_trial_runner import (
    build_eurusd_llm_trial_run_report,
    render_eurusd_llm_trial_run_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run EURUSD fail-closed LLM second-review trial skeleton")
    parser.add_argument("--readiness-json", type=Path, required=True)
    parser.add_argument("--approval-json", type=Path, required=True)
    parser.add_argument("--sample-artifacts-jsonl", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-llm-second-review-trial-run.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-llm-second-review-trial-run.md"))
    args = parser.parse_args()

    report = build_eurusd_llm_trial_run_report(
        readiness_json=args.readiness_json,
        approval_json=args.approval_json,
        sample_artifacts_jsonl=args.sample_artifacts_jsonl,
        output_jsonl=args.output_jsonl,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_eurusd_llm_trial_run_markdown(report), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "run_status": report.get("run_status"),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
