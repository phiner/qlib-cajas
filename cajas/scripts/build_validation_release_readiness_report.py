#!/usr/bin/env python3
"""Build validation release readiness dashboard report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_release_readiness import (
    build_validation_release_readiness_report,
    render_validation_release_readiness_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation release readiness report")
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--alias-sunset-review", required=True, type=Path)
    parser.add_argument("--runtime-release-cycle-report", required=True, type=Path)
    parser.add_argument("--runtime-variance-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--alias-removal-plan", type=Path)
    parser.add_argument("--consumer-evidence-closure-report", type=Path)
    parser.add_argument("--consumer-owner-handoff", type=Path)
    parser.add_argument("--consumer-owner-response-validation", type=Path)
    parser.add_argument("--consumer-evidence-candidate-report", type=Path)
    parser.add_argument("--evidence-candidate-approval-report", type=Path)
    parser.add_argument("--alias-sunset-schedule", type=Path)
    parser.add_argument("--canonical-evidence-update-plan", type=Path)
    parser.add_argument("--canonical-evidence-apply-report", type=Path)
    parser.add_argument("--applied-evidence-readiness", type=Path)
    parser.add_argument("--alias-fallback-removal-readiness", type=Path)
    parser.add_argument("--runtime-watch-triage-report", type=Path)
    parser.add_argument("--pytest-runtime-profile", type=Path)
    parser.add_argument("--alias-post-removal-closure", type=Path)
    parser.add_argument("--release-ready-closure", type=Path)
    parser.add_argument("--final-reviewer-packet", type=Path)
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
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_release_readiness_report(
        milestone_packet=args.milestone_packet,
        alias_sunset_review=args.alias_sunset_review,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
        runtime_variance_report=args.runtime_variance_report,
        runtime_edge_report=args.runtime_edge_report,
        runtime_budget_report=args.runtime_budget_report,
        alias_removal_plan=args.alias_removal_plan,
        consumer_evidence_closure_report=args.consumer_evidence_closure_report,
        consumer_owner_handoff=args.consumer_owner_handoff,
        consumer_owner_response_validation=args.consumer_owner_response_validation,
        consumer_evidence_candidate_report=args.consumer_evidence_candidate_report,
        evidence_candidate_approval_report=args.evidence_candidate_approval_report,
        alias_sunset_schedule=args.alias_sunset_schedule,
        canonical_evidence_update_plan=args.canonical_evidence_update_plan,
        canonical_evidence_apply_report=args.canonical_evidence_apply_report,
        applied_evidence_readiness=args.applied_evidence_readiness,
        alias_fallback_removal_readiness=args.alias_fallback_removal_readiness,
        runtime_watch_triage_report=args.runtime_watch_triage_report,
        pytest_runtime_profile=args.pytest_runtime_profile,
        alias_post_removal_closure=args.alias_post_removal_closure,
        release_ready_closure=args.release_ready_closure,
        final_reviewer_packet=args.final_reviewer_packet,
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
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_release_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
