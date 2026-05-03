#!/usr/bin/env python3
"""Build consumer owner handoff packet for unresolved alias evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_consumer_owner_handoff import (
    build_consumer_owner_handoff,
    render_consumer_owner_handoff_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build consumer owner handoff packet")
    parser.add_argument("--consumer-evidence", required=True, type=Path)
    parser.add_argument("--consumer-evidence-closure-report", type=Path)
    parser.add_argument("--alias-sunset-review", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_consumer_owner_handoff(
        consumer_evidence=args.consumer_evidence,
        consumer_evidence_closure_report=args.consumer_evidence_closure_report,
        alias_sunset_review=args.alias_sunset_review,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_consumer_owner_handoff_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
