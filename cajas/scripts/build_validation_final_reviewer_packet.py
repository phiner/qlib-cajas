#!/usr/bin/env python3
"""Build validation final reviewer packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_final_reviewer_packet import (
    build_validation_final_reviewer_packet,
    render_validation_final_reviewer_packet_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation final reviewer packet")
    parser.add_argument("--release-ready-closure", required=True, type=Path)
    parser.add_argument("--alias-post-removal-closure", required=True, type=Path)
    parser.add_argument("--runtime-variance-closure", required=True, type=Path)
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--review-bundle-manifest", required=True, type=Path)
    parser.add_argument("--manifest-compatibility-report", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--data-source-audit-report", required=True, type=Path)
    parser.add_argument("--maintenance-cadence", type=Path)
    parser.add_argument("--maintenance-checklist", type=Path)
    parser.add_argument("--optional-followups", type=Path)
    parser.add_argument("--maintenance-governance-closure", type=Path)
    parser.add_argument("--external-consumer-governance", type=Path)
    parser.add_argument("--external-consumer-evidence-closure-report", type=Path)
    parser.add_argument("--final-maintenance-archive-closure-report", type=Path)
    parser.add_argument("--post-freeze-handoff-seal-report", type=Path)
    parser.add_argument("--routine-release-cycle-stability-report", type=Path)
    parser.add_argument("--routine-stability-watch-closure", type=Path)
    parser.add_argument("--final-maintenance-handoff-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_final_reviewer_packet(
        release_ready_closure=args.release_ready_closure,
        alias_post_removal_closure=args.alias_post_removal_closure,
        runtime_variance_closure=args.runtime_variance_closure,
        release_readiness_report=args.release_readiness_report,
        milestone_packet=args.milestone_packet,
        review_bundle_manifest=args.review_bundle_manifest,
        manifest_compatibility_report=args.manifest_compatibility_report,
        runtime_budget_report=args.runtime_budget_report,
        runtime_edge_report=args.runtime_edge_report,
        data_source_audit_report=args.data_source_audit_report,
        maintenance_cadence=args.maintenance_cadence,
        maintenance_checklist=args.maintenance_checklist,
        optional_followups=args.optional_followups,
        maintenance_governance_closure=args.maintenance_governance_closure,
        external_consumer_governance=args.external_consumer_governance,
        external_consumer_evidence_closure_report=args.external_consumer_evidence_closure_report,
        final_maintenance_archive_closure_report=args.final_maintenance_archive_closure_report,
        post_freeze_handoff_seal_report=args.post_freeze_handoff_seal_report,
        routine_release_cycle_stability_report=args.routine_release_cycle_stability_report,
        routine_stability_watch_closure=args.routine_stability_watch_closure,
        final_maintenance_handoff_report=args.final_maintenance_handoff_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_final_reviewer_packet_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
