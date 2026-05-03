#!/usr/bin/env python3
"""Build EURUSD OHLC anomaly triage report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_ohlc_anomaly_triage import (
    build_validation_eurusd_ohlc_anomaly_triage,
    render_validation_eurusd_ohlc_anomaly_triage_markdown,
)


def _parse_inputs(raw: list[str]) -> list[Path]:
    out: list[Path] = []
    for token in raw:
        for p in token.split(","):
            v = p.strip()
            if v:
                out.append(Path(v))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD OHLC anomaly triage report")
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--price-side", default="Bid")
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_ohlc_anomaly_triage(
        input_paths=_parse_inputs(args.input),
        symbol=args.symbol,
        timeframe=args.timeframe,
        price_side=args.price_side,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_ohlc_anomaly_triage_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
