#!/usr/bin/env python3
"""Build EURUSD dataset contract report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_dataset_contract import (
    build_validation_eurusd_dataset_contract,
    render_validation_eurusd_dataset_contract_markdown,
)


def _parse_inputs(raw: list[str]) -> list[str]:
    out: list[str] = []
    for token in raw:
        out.extend(part.strip() for part in token.split(",") if part.strip())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD dataset contract report")
    parser.add_argument("--input", action="append", default=[], help="Repeatable or comma-separated input CSV paths")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--price-side", default="Bid")
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_dataset_contract(
        input_paths=_parse_inputs(args.input),
        symbol=args.symbol,
        timeframe=args.timeframe,
        price_side=args.price_side,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_eurusd_dataset_contract_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
