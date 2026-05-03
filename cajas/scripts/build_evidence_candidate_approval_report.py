#!/usr/bin/env python3
"""Build evidence candidate approval gate report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_evidence_candidate_approval import (
    build_evidence_candidate_approval_report,
    render_evidence_candidate_approval_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build evidence candidate approval report")
    parser.add_argument("--real-evidence", required=True, type=Path)
    parser.add_argument("--candidate-evidence", required=True, type=Path)
    parser.add_argument("--owner-response-validation", required=True, type=Path)
    parser.add_argument("--consumer-evidence-candidate-report", required=True, type=Path)
    parser.add_argument("--alias-sunset-review", required=True, type=Path)
    parser.add_argument("--alias-removal-plan", required=True, type=Path)
    parser.add_argument("--approval-file", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_evidence_candidate_approval_report(
        real_evidence=args.real_evidence,
        candidate_evidence=args.candidate_evidence,
        owner_response_validation=args.owner_response_validation,
        consumer_evidence_candidate_report=args.consumer_evidence_candidate_report,
        alias_sunset_review=args.alias_sunset_review,
        alias_removal_plan=args.alias_removal_plan,
        approval_file=args.approval_file,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_evidence_candidate_approval_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
