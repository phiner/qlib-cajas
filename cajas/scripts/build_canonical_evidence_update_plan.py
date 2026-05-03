#!/usr/bin/env python3
"""Build canonical evidence update plan report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_canonical_evidence_update_plan import (
    build_canonical_evidence_update_plan,
    render_canonical_evidence_update_plan_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build canonical evidence update plan")
    parser.add_argument("--real-evidence", required=True, type=Path)
    parser.add_argument("--candidate-evidence", required=True, type=Path)
    parser.add_argument("--evidence-candidate-approval-report", required=True, type=Path)
    parser.add_argument("--owner-response-validation", required=True, type=Path)
    parser.add_argument("--consumer-evidence-candidate-report", required=True, type=Path)
    parser.add_argument("--alias-sunset-schedule", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_canonical_evidence_update_plan(
        real_evidence=args.real_evidence,
        candidate_evidence=args.candidate_evidence,
        evidence_candidate_approval_report=args.evidence_candidate_approval_report,
        owner_response_validation=args.owner_response_validation,
        consumer_evidence_candidate_report=args.consumer_evidence_candidate_report,
        alias_sunset_schedule=args.alias_sunset_schedule,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_canonical_evidence_update_plan_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
