#!/usr/bin/env python3
"""Build validation external consumer evidence closure report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_external_consumer_evidence_closure import (
    build_validation_external_consumer_evidence_closure,
    render_validation_external_consumer_evidence_closure_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build external consumer evidence closure report")
    parser.add_argument("--alias-post-removal-closure", type=Path)
    parser.add_argument("--maintenance-governance-closure", type=Path)
    parser.add_argument("--release-readiness-report", type=Path)
    parser.add_argument("--optional-followups-report", type=Path)
    parser.add_argument("--consumer-owner-handoff", type=Path)
    parser.add_argument("--consumer-evidence-closure", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_external_consumer_evidence_closure(
        alias_post_removal_closure=args.alias_post_removal_closure,
        maintenance_governance_closure=args.maintenance_governance_closure,
        release_readiness_report=args.release_readiness_report,
        optional_followups_report=args.optional_followups_report,
        consumer_owner_handoff=args.consumer_owner_handoff,
        consumer_evidence_closure=args.consumer_evidence_closure,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_external_consumer_evidence_closure_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
