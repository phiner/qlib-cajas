#!/usr/bin/env python3
"""Build phase 2000+ validation milestone review packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_milestone_packet import (
    build_validation_milestone_packet,
    render_validation_milestone_packet_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation milestone packet")
    parser.add_argument("--review-bundle-root", required=True, type=Path)
    parser.add_argument("--alias-fallback-bundle-root", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--migration-readiness-report", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--data-source-audit-report", required=True, type=Path)
    parser.add_argument("--fast-timing-json", required=True, type=Path)
    parser.add_argument("--alias-sunset-review", type=Path)
    parser.add_argument("--runtime-release-cycle-report", type=Path)
    parser.add_argument("--runtime-variance-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args(argv)

    critical_inputs = [
        args.review_bundle_root / "final_status.json",
        args.alias_fallback_bundle_root / "final_status.json",
        args.runtime_edge_report,
        args.migration_readiness_report,
        args.runtime_budget_report,
        args.data_source_audit_report,
        args.fast_timing_json,
    ]
    missing = [str(p) for p in critical_inputs if not p.exists()]
    if missing and not args.warn_only:
        print(json.dumps({"status": "error", "missing": missing}), file=sys.stderr)
        return 1

    payload = build_validation_milestone_packet(
        review_bundle_root=args.review_bundle_root,
        alias_fallback_bundle_root=args.alias_fallback_bundle_root,
        runtime_edge_report=args.runtime_edge_report,
        migration_readiness_report=args.migration_readiness_report,
        runtime_budget_report=args.runtime_budget_report,
        data_source_audit_report=args.data_source_audit_report,
        fast_timing_json=args.fast_timing_json,
        alias_sunset_review=args.alias_sunset_review,
        runtime_release_cycle_report=args.runtime_release_cycle_report,
        runtime_variance_report=args.runtime_variance_report,
    )

    if missing:
        payload.setdefault("notes", []).append(f"Missing optional inputs tolerated under --warn-only: {missing}")

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_milestone_packet_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
