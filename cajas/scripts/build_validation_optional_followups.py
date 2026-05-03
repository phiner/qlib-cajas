#!/usr/bin/env python3
"""Build validation optional follow-ups report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_optional_followups import (
    build_validation_optional_followups,
    render_validation_optional_followups_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build validation optional follow-ups")
    parser.add_argument("--release-readiness-report", required=True, type=Path)
    parser.add_argument("--final-reviewer-packet", required=True, type=Path)
    parser.add_argument("--maintenance-cadence", required=True, type=Path)
    parser.add_argument("--external-consumer-evidence-closure-report", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_optional_followups(
        release_readiness_report=args.release_readiness_report,
        final_reviewer_packet=args.final_reviewer_packet,
        maintenance_cadence=args.maintenance_cadence,
        external_consumer_evidence_closure_report=args.external_consumer_evidence_closure_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_optional_followups_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
