#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.label_variant_trainer import train_label_variant_external_holdout


def main() -> int:
    p = argparse.ArgumentParser(description="Train external holdout model for a selected label variant.")
    p.add_argument("--train", required=True)
    p.add_argument("--holdout", required=True)
    p.add_argument("--label-col", required=True)
    p.add_argument("--label-mode", default="multiclass", choices=["multiclass", "binary_drop_flat"])
    p.add_argument("--output-dir", default="tmp/cajas/label_variant_runs")
    p.add_argument("--run-name", required=True)
    p.add_argument("--model-family", default="LightGBM")
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = train_label_variant_external_holdout(
        train_path=args.train,
        holdout_path=args.holdout,
        label_col=args.label_col,
        output_dir=args.output_dir,
        run_name=args.run_name,
        model_family=args.model_family,
        label_mode=args.label_mode,
        random_state=args.random_state,
    )
    payload = rep.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Label variant holdout training completed.")
        print(f"label col: {payload['label_col']}")
        print(f"label mode: {payload['label_mode']}")
        print(f"holdout macro_f1: {payload['holdout_metrics'].get('macro_f1')}")
        print("notice: classification-only; no trading/backtest/profit analysis")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
