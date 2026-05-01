#!/usr/bin/env python3
"""Train a controlled local baseline classifier for market-recognition research."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.local_baseline_trainer import train_local_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train local baseline classifier (no trading/backtest/profit outputs)."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_runs")
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--model-family", default="LightGBM")
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = train_local_baseline(
            config_path=args.config,
            output_dir=args.output_dir,
            run_name=args.run_name,
            input_override=args.input_override,
            model_family=args.model_family,
            random_state=args.random_state,
        )
    except (FileNotFoundError, ValueError, TypeError, RuntimeError, ImportError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("Local baseline training completed.")
    print(f"config name: {payload['config_name']}")
    print(f"run name: {payload['run_name']}")
    print(f"model family requested: {payload['model_family_requested']}")
    print(f"model family used: {payload['model_family_used']}")
    print(f"target label: {payload['target_label']}")
    print(f"feature count: {payload['feature_count']}")
    print(f"train rows: {payload['train_rows']}")
    print(f"valid rows: {payload['valid_rows']}")
    print(f"test rows: {payload['test_rows']}")
    print("training executed: true")
    print("model artifact created: true")
    print("prediction artifacts created: true")
    print("metrics artifacts created: true")
    print(f"run registry path: {payload['run_registry_path']}")
    print("artifact files:")
    for name in payload["artifact_files"]:
        print(f"  - {name}")
    print("warnings:")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    else:
        print("  - none")
    print("blockers:")
    if payload["blockers"]:
        for blocker in payload["blockers"]:
            print(f"  - {blocker}")
    else:
        print("  - none")
    print("notice: no trading/backtest/profit analysis performed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
