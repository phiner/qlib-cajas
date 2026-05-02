#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.flat_class_diagnosis import diagnose_flat_class


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Diagnose flat-class support and prediction behavior.")
    p.add_argument("--prediction-csv", required=True)
    p.add_argument("--split", required=True)
    p.add_argument("--flat-label", default="flat")
    p.add_argument("--chunk-size", type=int, default=50000, help="chunk size for counting")
    p.add_argument("--output-dir", default="tmp/cajas/flat_class_diagnosis")
    p.add_argument("--run-name", default="phase37_flat_class_diagnosis")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--artifact-row-limit", type=int, default=10000, help="max rows for artifact examples")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = diagnose_flat_class(
        prediction_csv=args.prediction_csv,
        split=args.split,
        flat_label=args.flat_label,
        chunk_size=args.chunk_size,
    )
    payload = report.to_dict()

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            print(f"ERROR: Refusing to overwrite existing output directory: {out_dir}", file=sys.stderr)
            return 1
        out_dir.mkdir(parents=True, exist_ok=False)
        _write_json(out_dir / "flat_class_diagnosis_report.json", payload)
        
        # Bounded read for artifact examples
        df = pd.read_csv(Path(args.prediction_csv).expanduser().resolve(), nrows=args.artifact_row_limit)
        m = (df["label"].astype(str) == args.flat_label) | (df["predicted_label"].astype(str) == args.flat_label)
        df[m].to_csv(out_dir / "flat_class_examples.csv", index=False)
        payload["artifact_output_dir"] = str(out_dir)
        payload["artifact_row_limit"] = args.artifact_row_limit

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Flat-class diagnosis completed.")
        print(f"split: {payload['split']}")
        print(f"flat support: {payload['flat_support']}")
        print(f"flat predictions: {payload['flat_predictions']}")
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
