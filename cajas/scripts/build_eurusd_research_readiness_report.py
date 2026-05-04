#!/usr/bin/env python3
"""Build EURUSD research readiness report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_research_readiness import (
    build_validation_eurusd_research_readiness,
    render_validation_eurusd_research_readiness_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD research readiness report")
    parser.add_argument("--base-maintenance-continuation-report", required=True, type=Path)
    parser.add_argument("--dataset-contract-report", required=True, type=Path)
    parser.add_argument("--dataset-audit-report", required=True, type=Path)
    parser.add_argument("--clean-dataset-view-report", type=Path)
    parser.add_argument("--pattern-candidate-pack-report", type=Path)
    parser.add_argument("--pattern-review-qa-report", type=Path)
    parser.add_argument("--pattern-label-schema-report", type=Path)
    parser.add_argument("--pattern-review-template-report", type=Path)
    parser.add_argument("--review-feedback-report", type=Path)
    parser.add_argument("--pattern-review-feedback-report", type=Path)
    parser.add_argument("--review-summary-report", type=Path)
    parser.add_argument("--pattern-review-summary-report", type=Path)
    parser.add_argument("--review-batch-report", type=Path)
    parser.add_argument("--review-guide-report", type=Path)
    parser.add_argument("--review-batch-completion-report", type=Path)
    parser.add_argument("--pattern-review-batch-completion-report", type=Path)
    parser.add_argument("--review-batch-merge-report", type=Path)
    parser.add_argument("--pattern-review-batch-merge-report", type=Path)
    parser.add_argument("--pattern-review-gui-report", type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args(argv)
    out_json = args.out_json or args.output_json
    out_md = args.out_md or args.output_md
    if out_json is None or out_md is None:
        parser.error("one of --out-json/--output-json and --out-md/--output-md must be provided")
    review_feedback_report = args.review_feedback_report or args.pattern_review_feedback_report
    review_summary_report = args.review_summary_report or args.pattern_review_summary_report
    review_batch_completion_report = (
        args.review_batch_completion_report or args.pattern_review_batch_completion_report
    )
    review_batch_merge_report = args.review_batch_merge_report or args.pattern_review_batch_merge_report

    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=args.base_maintenance_continuation_report,
        dataset_contract_report=args.dataset_contract_report,
        dataset_audit_report=args.dataset_audit_report,
        clean_dataset_view_report=args.clean_dataset_view_report,
        pattern_candidate_pack_report=args.pattern_candidate_pack_report,
        pattern_review_qa_report=args.pattern_review_qa_report,
        pattern_label_schema_report=args.pattern_label_schema_report,
        pattern_review_template_report=args.pattern_review_template_report,
        review_feedback_report=review_feedback_report,
        review_summary_report=review_summary_report,
        review_batch_report=args.review_batch_report,
        review_guide_report=args.review_guide_report,
        review_batch_completion_report=review_batch_completion_report,
        review_batch_merge_report=review_batch_merge_report,
        pattern_review_gui_report=args.pattern_review_gui_report,
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out_md.write_text(render_validation_eurusd_research_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(out_json), "out_md": str(out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
