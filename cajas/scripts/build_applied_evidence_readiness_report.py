#!/usr/bin/env python3
"""Build applied evidence readiness report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_applied_evidence_readiness import (
    build_applied_evidence_readiness_report,
    render_applied_evidence_readiness_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build applied evidence readiness report")
    parser.add_argument("--real-release-readiness", required=True, type=Path)
    parser.add_argument("--real-alias-sunset", required=True, type=Path)
    parser.add_argument("--applied-evidence-closure", required=True, type=Path)
    parser.add_argument("--applied-alias-sunset", required=True, type=Path)
    parser.add_argument("--applied-alias-removal-plan", required=True, type=Path)
    parser.add_argument("--applied-canonical-evidence-apply-report", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_applied_evidence_readiness_report(
        real_release_readiness=args.real_release_readiness,
        real_alias_sunset=args.real_alias_sunset,
        applied_evidence_closure=args.applied_evidence_closure,
        applied_alias_sunset=args.applied_alias_sunset,
        applied_alias_removal_plan=args.applied_alias_removal_plan,
        applied_canonical_evidence_apply_report=args.applied_canonical_evidence_apply_report,
        runtime_budget_report=args.runtime_budget_report,
        runtime_edge_report=args.runtime_edge_report,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_applied_evidence_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
