#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_run_comparison import compare_baseline_runs


def main() -> int:
    p = argparse.ArgumentParser(description="Compare baseline runs by classification metrics.")
    p.add_argument("--run-dir", action="append", required=True)
    p.add_argument("--primary-metric", default="test_macro_f1")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = compare_baseline_runs(run_dirs=args.run_dir, primary_metric=args.primary_metric)
    payload = rep.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Baseline comparison completed.")
        print(f"rows: {len(payload['rows'])}")
        print(f"best run: {payload['best_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
