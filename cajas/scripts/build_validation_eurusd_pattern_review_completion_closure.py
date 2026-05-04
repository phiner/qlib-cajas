#!/usr/bin/env python3
"""Build EURUSD 15m review completion closure report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_completion_closure import (
    build_review_completion_closure_report,
    render_review_completion_closure_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD 15m review completion closure report")
    parser.add_argument("--batch-csv", type=Path, required=True)
    parser.add_argument("--completed-csv", type=Path, required=True)
    parser.add_argument("--label-schema", type=Path, required=True)
    parser.add_argument("--audit-jsonl", type=Path)
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-pattern-review-completion-closure.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-pattern-review-completion-closure.md"))
    args = parser.parse_args()

    payload = build_review_completion_closure_report(
        batch_csv=args.batch_csv,
        completed_csv=args.completed_csv,
        label_schema_json=args.label_schema,
        audit_jsonl=args.audit_jsonl,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_review_completion_closure_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
