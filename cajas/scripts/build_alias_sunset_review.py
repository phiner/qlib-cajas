#!/usr/bin/env python3
"""Build alias sunset readiness review report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_alias_sunset_review import (
    build_alias_sunset_review,
    render_alias_sunset_review_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build alias sunset review")
    parser.add_argument("--migration-readiness-report", required=True, type=Path)
    parser.add_argument("--milestone-packet", required=True, type=Path)
    parser.add_argument(
        "--external-consumer-status",
        required=False,
        choices=["unknown", "confirmed_clear", "requires_alias"],
    )
    parser.add_argument("--consumer-evidence", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_alias_sunset_review(
        migration_readiness_report=args.migration_readiness_report,
        milestone_packet=args.milestone_packet,
        external_consumer_status=args.external_consumer_status,
        consumer_evidence=args.consumer_evidence,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_alias_sunset_review_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
