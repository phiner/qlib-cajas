#!/usr/bin/env python3
"""Build deterministic LLM-ready EURUSD review sample artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_llm_review_artifacts import (
    build_llm_review_artifacts_report,
    render_llm_review_artifacts_markdown,
    write_artifacts_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic LLM-ready EURUSD review sample artifacts")
    parser.add_argument("--batch-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"))
    parser.add_argument("--clean-view-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--completed-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"))
    parser.add_argument("--policy-doc", type=Path, default=Path("cajas/docs/eurusd_review_language_policy.md"))
    parser.add_argument("--output-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.md"))
    args = parser.parse_args()

    artifacts, report = build_llm_review_artifacts_report(
        batch_csv=args.batch_csv,
        clean_view_csv=args.clean_view_csv,
        completed_csv=args.completed_csv,
        policy_doc=args.policy_doc,
    )
    write_artifacts_jsonl(args.output_jsonl, artifacts)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_llm_review_artifacts_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report["report_status"], "rows": len(artifacts), "output_jsonl": str(args.output_jsonl)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
