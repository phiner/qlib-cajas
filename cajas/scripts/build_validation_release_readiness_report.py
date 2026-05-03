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
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_release_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
