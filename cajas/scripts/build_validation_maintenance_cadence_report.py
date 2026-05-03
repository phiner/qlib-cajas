#!/usr/bin/env python3
"""Build validation maintenance cadence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_maintenance_cadence import (
    build_validation_maintenance_cadence_report,
    render_validation_maintenance_cadence_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation maintenance cadence report")
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--release-ready-closure", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--alias-post-removal-closure", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--runtime-release-cycle-report", required=True, type=Path)
    parser.add_argument("--data-source-audit-report", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_maintenance_cadence_report(
        release_readiness_report=args.release_readiness_report,
        release_ready_closure=args.release_ready_closure,
        final_reviewer_packet=args.final_reviewer_packet,
        alias_post_removal_closure=args.alias_post_removal_closure,
        runtime_budget_report=args.runtime_budget_report,
        runtime_edge_report=args.runtime_edge_report,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
        data_source_audit_report=args.data_source_audit_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_maintenance_cadence_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
