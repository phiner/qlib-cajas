#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.error_slice_analysis import analyze_error_slices


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze prediction errors by metadata/confidence slices.")
    p.add_argument("--prediction-csv", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/error_slice_analysis")
    p.add_argument("--run-name", default="phase52_error_slice_analysis")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = analyze_error_slices(prediction_csv=args.prediction_csv, output_dir=args.output_dir, run_name=args.run_name)
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Error slice analysis completed.")
        print(f"slice rows: {len(rep.get('slices', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
