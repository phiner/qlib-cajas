#!/usr/bin/env python3
"""Build alias post-removal closure packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_alias_post_removal_closure import (
    build_validation_alias_post_removal_closure,
    render_validation_alias_post_removal_closure_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build alias post-removal closure report")
    parser.add_argument("--review-bundle-manifest", required=True, type=Path)
    parser.add_argument("--manifest-compatibility-report", required=True, type=Path)
    parser.add_argument("--alias-fallback-removal-readiness", required=True, type=Path)
    parser.add_argument("--runtime-budget-report", required=True, type=Path)
    parser.add_argument("--runtime-edge-report", required=True, type=Path)
    parser.add_argument("--data-source-audit-report", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_alias_post_removal_closure(
        review_bundle_manifest=args.review_bundle_manifest,
        manifest_compatibility_report=args.manifest_compatibility_report,
        alias_fallback_removal_readiness=args.alias_fallback_removal_readiness,
        runtime_budget_report=args.runtime_budget_report,
        runtime_edge_report=args.runtime_edge_report,
        data_source_audit_report=args.data_source_audit_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_alias_post_removal_closure_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
