#!/usr/bin/env python3
"""Build validation post-freeze handoff seal report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_post_freeze_handoff_seal import (
    build_validation_post_freeze_handoff_seal,
    render_validation_post_freeze_handoff_seal_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build post-freeze handoff seal report")
    parser.add_argument("--external-consumer-evidence-closure-report", type=Path)
    parser.add_argument("--final-maintenance-archive-closure-report", type=Path)
    parser.add_argument("--maintenance-governance-closure-report", type=Path)
    parser.add_argument("--maintenance-checklist-report", type=Path)
    parser.add_argument("--optional-followups-report", type=Path)
    parser.add_argument("--release-readiness-report", type=Path)
    parser.add_argument("--final-reviewer-packet-report", type=Path)
    parser.add_argument("--milestone-packet-report", type=Path)
    parser.add_argument("--alias-post-removal-closure-report", type=Path)
    parser.add_argument("--runtime-release-cycle-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_post_freeze_handoff_seal(
        external_consumer_evidence_closure_report=args.external_consumer_evidence_closure_report,
        final_maintenance_archive_closure_report=args.final_maintenance_archive_closure_report,
        maintenance_governance_closure_report=args.maintenance_governance_closure_report,
        maintenance_checklist_report=args.maintenance_checklist_report,
        optional_followups_report=args.optional_followups_report,
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet_report=args.final_reviewer_packet_report,
        milestone_packet_report=args.milestone_packet_report,
        alias_post_removal_closure_report=args.alias_post_removal_closure_report,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_post_freeze_handoff_seal_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
