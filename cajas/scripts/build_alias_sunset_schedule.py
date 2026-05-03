#!/usr/bin/env python3
"""Build alias sunset scheduling packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_alias_sunset_schedule import (
    build_alias_sunset_schedule,
    render_alias_sunset_schedule_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build alias sunset schedule packet")
    parser.add_argument("--evidence-candidate-approval-report", required=True, type=Path)
    parser.add_argument("--alias-removal-plan", required=True, type=Path)
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_alias_sunset_schedule(
        evidence_candidate_approval_report=args.evidence_candidate_approval_report,
        alias_removal_plan=args.alias_removal_plan,
        release_readiness_report=args.release_readiness_report,
        milestone_packet=args.milestone_packet,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_alias_sunset_schedule_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
