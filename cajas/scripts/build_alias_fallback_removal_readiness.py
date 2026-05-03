#!/usr/bin/env python3
"""Build alias fallback removal readiness packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_alias_fallback_removal_readiness import (
    build_alias_fallback_removal_readiness,
    render_alias_fallback_removal_readiness_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build alias fallback removal readiness")
    parser.add_argument("--applied-evidence-readiness", required=True, type=Path)
    parser.add_argument("--applied-alias-removal-plan", type=Path)
    parser.add_argument("--applied-alias-sunset-review", type=Path)
    parser.add_argument("--alias-removal-plan", type=Path)
    parser.add_argument("--alias-sunset-review", type=Path)
    parser.add_argument("--manifest-compatibility-report", type=Path)
    parser.add_argument("--review-bundle-manifest", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    removal_plan = args.applied_alias_removal_plan or args.alias_removal_plan
    sunset_review = args.applied_alias_sunset_review or args.alias_sunset_review
    if not removal_plan or not sunset_review:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": "one of --applied-alias-removal-plan/--alias-removal-plan and "
                    "--applied-alias-sunset-review/--alias-sunset-review is required",
                }
            ),
            file=sys.stderr,
        )
        return 1

    payload = build_alias_fallback_removal_readiness(
        applied_evidence_readiness=args.applied_evidence_readiness,
        applied_alias_removal_plan=removal_plan,
        applied_alias_sunset_review=sunset_review,
        manifest_compatibility_report=args.manifest_compatibility_report,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_alias_fallback_removal_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
