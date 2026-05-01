#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.external_holdout_trainer import train_external_holdout_baseline


def main() -> int:
    p = argparse.ArgumentParser(description="Train external holdout baseline (train 2020-2024, validate 2025).")
    p.add_argument("--train", required=True)
    p.add_argument("--holdout", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--model-family", default="LightGBM")
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = train_external_holdout_baseline(
        train_path=args.train,
        holdout_path=args.holdout,
        output_dir=args.output_dir,
        run_name=args.run_name,
        model_family=args.model_family,
        random_state=args.random_state,
    )
    payload = report.to_dict()

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("External holdout baseline training completed.")
    print(f"run name: {payload['run_name']}")
    print(f"model family requested: {payload['model_family_requested']}")
    print(f"model family used: {payload['model_family_used']}")
    print(f"train rows: {payload['train_rows']}")
    print(f"holdout rows: {payload['holdout_rows']}")
    print(f"feature count: {payload['feature_count']}")
    print(f"holdout metrics accuracy: {payload['holdout_metrics'].get('accuracy')}")
    print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
