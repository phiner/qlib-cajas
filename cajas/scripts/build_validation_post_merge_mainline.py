#!/usr/bin/env python3
"""Build post-merge mainline validation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_post_merge_mainline import (
    build_validation_post_merge_mainline,
    render_validation_post_merge_mainline_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build post-merge mainline validation report")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--source-branch", default="phase-post-merge-research-next")
    parser.add_argument("--merge-confirmed", action="store_true")
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--final-maintenance-handoff-report", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument("--routine-stability-watch-closure-report", required=True, type=Path)
    parser.add_argument("--optional-followups-report", required=True, type=Path)
    parser.add_argument("--alias-post-removal-closure-report", type=Path)
    parser.add_argument("--review-bundle-manifest", type=Path)
    parser.add_argument("--fast-validation-timing-json", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_post_merge_mainline(
        branch=args.branch,
        source_branch=args.source_branch,
        merge_confirmed=args.merge_confirmed,
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet=args.final_reviewer_packet,
        final_maintenance_handoff_report=args.final_maintenance_handoff_report,
        milestone_packet=args.milestone_packet,
        routine_stability_watch_closure_report=args.routine_stability_watch_closure_report,
        optional_followups_report=args.optional_followups_report,
        alias_post_removal_closure_report=args.alias_post_removal_closure_report,
        review_bundle_manifest=args.review_bundle_manifest,
        fast_validation_timing_json=args.fast_validation_timing_json,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_post_merge_mainline_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
