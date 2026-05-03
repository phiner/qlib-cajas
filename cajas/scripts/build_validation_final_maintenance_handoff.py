#!/usr/bin/env python3
"""Build final maintenance handoff report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_final_maintenance_handoff import (
    build_validation_final_maintenance_handoff,
    render_validation_final_maintenance_handoff_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build final maintenance handoff report")
    parser.add_argument("--branch", default="phase-post-merge-research-next")
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--routine-stability-watch-closure", type=Path)
    parser.add_argument("--post-freeze-handoff-seal-report", type=Path)
    parser.add_argument("--final-maintenance-archive-closure-report", type=Path)
    parser.add_argument("--external-consumer-evidence-closure-report", type=Path)
    parser.add_argument("--alias-post-removal-closure-report", type=Path)
    parser.add_argument("--optional-followups-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_final_maintenance_handoff(
        branch=args.branch,
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet=args.final_reviewer_packet,
        milestone_packet=args.milestone_packet,
        routine_stability_watch_closure=args.routine_stability_watch_closure,
        post_freeze_handoff_seal_report=args.post_freeze_handoff_seal_report,
        final_maintenance_archive_closure_report=args.final_maintenance_archive_closure_report,
        external_consumer_evidence_closure_report=args.external_consumer_evidence_closure_report,
        alias_post_removal_closure_report=args.alias_post_removal_closure_report,
        optional_followups_report=args.optional_followups_report,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_final_maintenance_handoff_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
