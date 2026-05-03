#!/usr/bin/env python3
"""Build alias fallback removal plan report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_alias_removal_plan import (
    build_alias_removal_plan,
    render_alias_removal_plan_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build alias removal plan")
    parser.add_argument("--alias-sunset-review", required=True, type=Path)
    parser.add_argument("--migration-readiness-report", required=True, type=Path)
    parser.add_argument("--release-readiness-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_alias_removal_plan(
        alias_sunset_review=args.alias_sunset_review,
        migration_readiness_report=args.migration_readiness_report,
        release_readiness_report=args.release_readiness_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_alias_removal_plan_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
