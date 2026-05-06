#!/usr/bin/env python3
"""Build EURUSD first real unified review batch report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_first_real_review_batch import (
    build_first_real_review_batch_report,
    render_first_real_review_batch_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD first real review batch report")
    parser.add_argument("--completed-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"))
    parser.add_argument("--events-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl"))
    parser.add_argument("--llm-artifact-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl"))
    parser.add_argument("--human-review-quality-json", type=Path, default=Path("tmp/validation-eurusd-human-review-quality.json"))
    parser.add_argument("--llm-artifact-report-json", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.json"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--minimum-total-reviewed", type=int, default=10)
    parser.add_argument("--minimum-new-since-smoke", type=int, default=7)
    parser.add_argument("--minimum-layer-feedback-ratio", type=float, default=0.8)
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-first-real-review-batch.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-first-real-review-batch.md"))
    args = parser.parse_args()

    payload = build_first_real_review_batch_report(
        completed_csv=args.completed_csv,
        review_events_jsonl=args.events_jsonl,
        llm_artifact_jsonl=args.llm_artifact_jsonl,
        human_review_quality_json=args.human_review_quality_json,
        llm_artifact_report_json=args.llm_artifact_report_json,
        trial_approval_json=args.trial_approval_json,
        minimum_total_reviewed=args.minimum_total_reviewed,
        minimum_new_since_smoke=args.minimum_new_since_smoke,
        minimum_layer_feedback_ratio=args.minimum_layer_feedback_ratio,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output_md.write_text(render_first_real_review_batch_markdown(payload), encoding="utf-8")
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
