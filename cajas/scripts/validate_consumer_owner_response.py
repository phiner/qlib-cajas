#!/usr/bin/env python3
"""Validate consumer owner response payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_consumer_owner_response import (
    render_consumer_owner_response_validation_markdown,
    validate_consumer_owner_response,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate consumer owner response")
    parser.add_argument("--consumer-evidence", required=True, type=Path)
    parser.add_argument("--owner-response", required=True, type=Path)
    parser.add_argument("--consumer-owner-handoff", type=Path)
    parser.add_argument("--apply-to-out", type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = validate_consumer_owner_response(
        consumer_evidence=args.consumer_evidence,
        owner_response=args.owner_response,
        consumer_owner_handoff=args.consumer_owner_handoff,
        apply_to_out=args.apply_to_out,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_consumer_owner_response_validation_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
