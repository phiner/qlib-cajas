#!/usr/bin/env python3
"""Build EURUSD bilingual language-boundary validation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_language_boundary import (
    build_language_boundary_report,
    format_language_boundary_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD language-boundary validation report")
    parser.add_argument(
        "--policy-doc",
        type=Path,
        default=Path("cajas/docs/eurusd_review_language_policy.md"),
    )
    parser.add_argument(
        "--kickoff-doc",
        type=Path,
        default=Path("cajas/docs/eurusd_pattern_research_kickoff.md"),
    )
    parser.add_argument(
        "--roadmap-doc",
        type=Path,
        default=Path("tasks/eurusd_15m_research_end_to_end_roadmap.md"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("tmp/validation-eurusd-language-boundary.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("tmp/validation-eurusd-language-boundary.md"),
    )
    args = parser.parse_args()

    report = build_language_boundary_report(
        policy_doc=args.policy_doc,
        kickoff_doc=args.kickoff_doc,
        roadmap_doc=args.roadmap_doc,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(format_language_boundary_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report["status"], "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
