#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_dataset_contract_builder import build_qlib_dataset_contract


def main() -> int:
    p = argparse.ArgumentParser(description="Build offline Qlib dataset contract from a feature/label CSV.")
    p.add_argument("--input-csv", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dataset-id", required=True)
    p.add_argument("--instrument-col", default="instrument")
    p.add_argument("--datetime-col", default="datetime")
    p.add_argument("--label-col", action="append", dest="label_cols")
    args = p.parse_args()

    contract = build_qlib_dataset_contract(
        input_csv=args.input_csv,
        out_path=args.out,
        dataset_id=args.dataset_id,
        instrument_col=args.instrument_col,
        datetime_col=args.datetime_col,
        label_columns=args.label_cols,
    )
    print("Qlib dataset contract completed.")
    print(f"output: {Path(args.out).expanduser().resolve()}")
    print(f"readiness_status: {contract['readiness_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
