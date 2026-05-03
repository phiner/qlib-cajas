#!/usr/bin/env python3
"""Build validation maintenance governance closure report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_maintenance_governance_closure import (
    build_validation_maintenance_governance_closure,
    render_validation_maintenance_governance_closure_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build maintenance governance closure")
    parser.add_argument("--maintenance-checklist", required=True, type=Path)
    parser.add_argument("--optional-followups", required=True, type=Path)
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--alias-post-removal-closure", required=True, type=Path)
    parser.add_argument("--runtime-release-cycle-report", type=Path)
    parser.add_argument("--runtime-variance-closure-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_maintenance_governance_closure(
        maintenance_checklist=args.maintenance_checklist,
        optional_followups=args.optional_followups,
        release_readiness_report=args.release_readiness_report,
        milestone_packet=args.milestone_packet,
        final_reviewer_packet=args.final_reviewer_packet,
        alias_post_removal_closure=args.alias_post_removal_closure,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
        runtime_variance_closure_report=args.runtime_variance_closure_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_maintenance_governance_closure_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
