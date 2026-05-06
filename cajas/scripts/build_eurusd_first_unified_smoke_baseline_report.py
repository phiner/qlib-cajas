#!/usr/bin/env python3
"""Build EURUSD first unified smoke baseline report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_first_unified_smoke_baseline import (
    build_first_unified_smoke_baseline_report,
    render_first_unified_smoke_baseline_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD first unified smoke baseline report")
    parser.add_argument("--completed-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"))
    parser.add_argument("--events-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl"))
    parser.add_argument("--llm-artifact-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl"))
    parser.add_argument("--smoke-report-json", type=Path, default=Path("tmp/validation-eurusd-human-review-smoke-session.json"))
    parser.add_argument("--quality-report-json", type=Path, default=Path("tmp/validation-eurusd-human-review-quality.json"))
    parser.add_argument("--llm-artifact-report-json", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.json"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--minimum-reviewed-samples", type=int, default=3)
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-first-unified-smoke-baseline.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-first-unified-smoke-baseline.md"))
    args = parser.parse_args()

    payload = build_first_unified_smoke_baseline_report(
        completed_csv=args.completed_csv,
        review_events_jsonl=args.events_jsonl,
        llm_artifact_jsonl=args.llm_artifact_jsonl,
        smoke_report_json=args.smoke_report_json,
        quality_report_json=args.quality_report_json,
        llm_artifact_report_json=args.llm_artifact_report_json,
        trial_approval_json=args.trial_approval_json,
        minimum_reviewed_samples=args.minimum_reviewed_samples,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output_md.write_text(render_first_unified_smoke_baseline_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "report_status": payload.get("report_status"),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
