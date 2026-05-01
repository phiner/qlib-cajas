#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.calibration_analysis import analyze_calibration, write_calibration_artifacts


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze prediction calibration buckets.")
    p.add_argument("--prediction-csv", required=True)
    p.add_argument("--split", default="holdout")
    p.add_argument("--bucket-count", type=int, default=10)
    p.add_argument("--output-dir", default="tmp/cajas/calibration_analysis")
    p.add_argument("--run-name", default="phase49_calibration_analysis")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = analyze_calibration(prediction_csv=args.prediction_csv, split=args.split, bucket_count=args.bucket_count)
    if args.write_artifacts:
        out = Path(args.output_dir).expanduser().resolve() / args.run_name
        out.mkdir(parents=True, exist_ok=False)
        write_calibration_artifacts(report=rep, output_dir=out)
        rep["output_dir"] = str(out)
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Calibration analysis completed.")
        print(f"ece_like: {rep.get('ece_like')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
