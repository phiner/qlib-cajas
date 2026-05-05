#!/usr/bin/env python3
"""Build EURUSD real LLM integration readiness report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_real_llm_integration_readiness import (
    build_real_llm_integration_readiness_report,
    render_real_llm_integration_readiness_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD real LLM integration readiness report")
    parser.add_argument("--language-boundary-json", type=Path, default=Path("tmp/validation-eurusd-language-boundary.json"))
    parser.add_argument("--zh-rationale-json", type=Path, default=Path("tmp/validation-eurusd-zh-rationale-fields.json"))
    parser.add_argument("--llm-artifacts-json", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.json"))
    parser.add_argument("--llm-second-review-json", type=Path, default=Path("tmp/validation-eurusd-llm-second-review.json"))
    parser.add_argument("--standard-v0-json", type=Path, default=Path("tmp/validation-eurusd-review-standard-v0.json"))
    parser.add_argument("--fixture-drill-json", type=Path, default=Path("tmp/validation-eurusd-llm-second-review-fixture.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-real-llm-integration-readiness.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-real-llm-integration-readiness.md"))
    args = parser.parse_args()

    docs_to_check = [
        Path("cajas/docs/eurusd_llm_second_review_protocol.md"),
        Path("cajas/docs/eurusd_llm_review_standard_v0.md"),
        Path("cajas/docs/eurusd_review_language_policy.md"),
        Path("cajas/docs/eurusd_pattern_research_kickoff.md"),
        Path("tasks/eurusd_15m_research_end_to_end_roadmap.md"),
    ]
    files_to_scan = [
        Path("cajas/scripts/build_eurusd_llm_second_review_report.py"),
        Path("cajas/reports/validation_eurusd_llm_second_review.py"),
        Path("cajas/reports/validation_eurusd_llm_review_artifacts.py"),
    ]
    report = build_real_llm_integration_readiness_report(
        language_boundary_json=args.language_boundary_json,
        zh_rationale_json=args.zh_rationale_json,
        llm_artifacts_json=args.llm_artifacts_json,
        llm_second_review_json=args.llm_second_review_json,
        standard_v0_json=args.standard_v0_json,
        fixture_drill_json=args.fixture_drill_json,
        docs_to_check=docs_to_check,
        files_to_scan_for_live_llm=files_to_scan,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_real_llm_integration_readiness_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "readiness_status": report.get("status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
