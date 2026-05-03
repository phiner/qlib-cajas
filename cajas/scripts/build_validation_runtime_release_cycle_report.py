#!/usr/bin/env python3
"""Build release-cycle runtime monitor report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_runtime_release_cycle import (
    build_validation_runtime_release_cycle_report,
    render_validation_runtime_release_cycle_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation runtime release-cycle report")
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--fast-timing-json", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_runtime_release_cycle_report(
        runtime_edge_report=args.runtime_edge_report,
        runtime_budget_report=args.runtime_budget_report,
        fast_timing_json=args.fast_timing_json,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_runtime_release_cycle_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
