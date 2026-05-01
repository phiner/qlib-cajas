#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.baseline_report_pack import build_baseline_report_pack


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a baseline report pack from an existing run.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--top-k-features", type=int, default=30)
    p.add_argument("--json", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    report = build_baseline_report_pack(
        run_dir=args.run_dir,
        output_dir=args.output_dir,
        run_name=args.run_name,
        write_artifacts=True,
        top_k_features=args.top_k_features,
    )
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0
    print("Baseline report pack completed.")
    print(f"run name: {args.run_name}")
    print(f"model family: {payload['model_family']}")
    print(f"target label: {payload['target_label']}")
    print(f"valid accuracy: {payload['valid_metrics'].get('accuracy')}")
    print(f"test accuracy: {payload['test_metrics'].get('accuracy')}")
    print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
