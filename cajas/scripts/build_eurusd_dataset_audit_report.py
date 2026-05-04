#!/usr/bin/env python3
"""Build EURUSD dataset audit report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_dataset_audit import (
    build_validation_eurusd_dataset_audit,
    render_validation_eurusd_dataset_audit_markdown,
)


def _parse_inputs(raw: list[str]) -> list[Path]:
    items: list[Path] = []
    for token in raw:
        for part in token.split(","):
            p = part.strip()
            if p:
                items.append(Path(p))
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD dataset audit report")
    parser.add_argument("--input", action="append", required=True, help="Repeatable or comma-separated CSV paths")
    parser.add_argument("--min-rows", type=int, default=20, help="Minimum rows required per file for non-blocked status")
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_dataset_audit(input_paths=_parse_inputs(args.input), min_rows=args.min_rows)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_eurusd_dataset_audit_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
