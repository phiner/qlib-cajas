#!/usr/bin/env python3
"""Create completed feedback template CSV from inspection packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_market_state_inspection_packet import FEEDBACK_FIELDS


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD market-state inspection feedback template")
    parser.add_argument("--inspection-packet-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    if not args.inspection_packet_csv.exists():
        raise SystemExit("inspection_packet_csv_missing")
    df = pd.read_csv(args.inspection_packet_csv)
    for col in FEEDBACK_FIELDS:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = ""
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    print(json.dumps({"status": "ok", "row_count": int(len(df)), "output_csv": str(args.output_csv)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
