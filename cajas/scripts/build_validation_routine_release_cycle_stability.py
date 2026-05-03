#!/usr/bin/env python3
"""Build routine release-cycle stability report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_routine_release_cycle_stability import (
    build_validation_routine_release_cycle_stability,
    render_validation_routine_release_cycle_stability_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build routine release-cycle stability report")
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--runtime-release-cycle-report", required=True, type=Path)
    parser.add_argument("--runtime-variance-closure-report", required=True, type=Path)
    parser.add_argument("--data-source-audit-report", required=True, type=Path)
    parser.add_argument("--path-hygiene-report", type=Path)
    parser.add_argument("--maintenance-checklist", type=Path)
    parser.add_argument("--maintenance-governance-closure", type=Path)
    parser.add_argument("--final-maintenance-archive-closure-report", type=Path)
    parser.add_argument("--external-consumer-evidence-closure-report", type=Path)
    parser.add_argument("--post-freeze-handoff-seal-report", type=Path)
    parser.add_argument("--optional-followups", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_routine_release_cycle_stability(
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet=args.final_reviewer_packet,
        milestone_packet=args.milestone_packet,
        runtime_budget_report=args.runtime_budget_report,
        runtime_edge_report=args.runtime_edge_report,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
        runtime_variance_closure_report=args.runtime_variance_closure_report,
        data_source_audit_report=args.data_source_audit_report,
        path_hygiene_report=args.path_hygiene_report,
        maintenance_checklist=args.maintenance_checklist,
        maintenance_governance_closure=args.maintenance_governance_closure,
        final_maintenance_archive_closure_report=args.final_maintenance_archive_closure_report,
        external_consumer_evidence_closure_report=args.external_consumer_evidence_closure_report,
        post_freeze_handoff_seal_report=args.post_freeze_handoff_seal_report,
        optional_followups=args.optional_followups,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_routine_release_cycle_stability_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
