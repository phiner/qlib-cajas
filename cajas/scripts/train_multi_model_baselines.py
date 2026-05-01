#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.multi_model_baseline import run_multi_model_baseline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train controlled multi-model local baselines.")
    p.add_argument("--config", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--model-family", action="append", dest="model_families", required=True)
    p.add_argument("--primary-metric", default="test_macro_f1")
    p.add_argument("--input-override", default=None)
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--json", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    report = run_multi_model_baseline(
        config_path=args.config,
        output_dir=args.output_dir,
        run_name=args.run_name,
        model_families=args.model_families,
        primary_metric=args.primary_metric,
        input_override=args.input_override,
        random_state=args.random_state,
    )
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0
    print("Multi-model baseline completed.")
    print("model families requested: " + ", ".join(payload["model_families_requested"]))
    completed = sum(1 for row in payload["comparison"].get("model_status", []) if row.get("status") == "completed")
    failed = sum(1 for row in payload["comparison"].get("model_status", []) if row.get("status") == "failed")
    skipped = sum(1 for row in payload["comparison"].get("model_status", []) if row.get("status") == "skipped")
    print("model runs completed: " + str(completed))
    print("model runs failed: " + str(failed))
    print("model runs skipped: " + str(skipped))
    print("best model: " + str(payload["best_model_by_primary_metric"]))
    print("primary metric: " + payload["primary_metric"])
    print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
