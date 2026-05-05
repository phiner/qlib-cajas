#!/usr/bin/env python3
"""Build human-governed EURUSD review standard v0 validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_review_standard_v0 import (
    build_review_standard_v0_report,
    render_review_standard_v0_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD review standard v0 validation report")
    parser.add_argument("--standard-doc", type=Path, default=Path("cajas/docs/eurusd_llm_review_standard_v0.md"))
    parser.add_argument("--example-jsonl", type=Path, default=Path("cajas/data_examples/eurusd_review_standard_v0_examples.jsonl"))
    parser.add_argument("--language-policy-doc", type=Path, default=Path("cajas/docs/eurusd_review_language_policy.md"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-review-standard-v0.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-review-standard-v0.md"))
    args = parser.parse_args()

    report = build_review_standard_v0_report(
        standard_doc=args.standard_doc,
        example_jsonl=args.example_jsonl,
        language_policy_doc=args.language_policy_doc,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_review_standard_v0_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
