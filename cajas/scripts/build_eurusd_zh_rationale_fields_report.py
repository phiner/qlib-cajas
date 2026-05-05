#!/usr/bin/env python3
"""Build EURUSD zh rationale fields validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_zh_rationale_fields import (
    build_zh_rationale_fields_report,
    format_zh_rationale_fields_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD zh rationale fields validation report")
    parser.add_argument("--policy-doc", type=Path, default=Path("cajas/docs/eurusd_review_language_policy.md"))
    parser.add_argument("--app-path", type=Path, default=Path("cajas/apps/eurusd_pattern_review_app.py"))
    parser.add_argument("--helper-path", type=Path, default=Path("cajas/research/eurusd_pattern_review_gui.py"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-zh-rationale-fields.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-zh-rationale-fields.md"))
    args = parser.parse_args()

    report = build_zh_rationale_fields_report(
        policy_doc_path=args.policy_doc,
        app_path=args.app_path,
        helper_path=args.helper_path,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(format_zh_rationale_fields_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report["status"], "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
