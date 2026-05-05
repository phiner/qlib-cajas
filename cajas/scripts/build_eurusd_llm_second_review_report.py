#!/usr/bin/env python3
"""Build offline EURUSD LLM second-review protocol/output report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_llm_second_review import (
    build_llm_second_review_report,
    render_llm_second_review_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD LLM second review report")
    parser.add_argument("--sample-artifacts-jsonl", type=Path, required=True)
    parser.add_argument("--llm-outputs-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_llm_second_review_outputs.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-llm-second-review.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-llm-second-review.md"))
    parser.add_argument("--min-output-coverage", type=float, default=0.8)
    parser.add_argument("--max-high-conf-disagreement-rate", type=float, default=0.2)
    args = parser.parse_args()

    report = build_llm_second_review_report(
        sample_artifacts_jsonl=args.sample_artifacts_jsonl,
        llm_outputs_jsonl=args.llm_outputs_jsonl,
        min_output_coverage=args.min_output_coverage,
        max_high_conf_disagreement_rate=args.max_high_conf_disagreement_rate,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_llm_second_review_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
