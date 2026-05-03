#!/usr/bin/env python3
"""Build routine maintenance continuation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_routine_maintenance_continuation import (
    build_validation_routine_maintenance_continuation,
    render_validation_routine_maintenance_continuation_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build routine maintenance continuation report")
    parser.add_argument("--post-merge-mainline-report", required=True, type=Path)
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--optional-followups-report", type=Path)
    parser.add_argument("--review-bundle-manifest", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_routine_maintenance_continuation(
        post_merge_mainline_report=args.post_merge_mainline_report,
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet=args.final_reviewer_packet,
        milestone_packet=args.milestone_packet,
        optional_followups_report=args.optional_followups_report,
        review_bundle_manifest=args.review_bundle_manifest,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_routine_maintenance_continuation_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
