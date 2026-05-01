#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.feature_set_comparison import run_feature_set_comparison


def main() -> int:
    p = argparse.ArgumentParser(description="Compare external holdout runs across feature sets.")
    p.add_argument("--train", required=True)
    p.add_argument("--holdout", required=True)
    p.add_argument("--label-col", required=True)
    p.add_argument("--feature-set", action="append", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/feature_set_comparisons")
    p.add_argument("--run-name", default="phase48_feature_set_comparison")
    p.add_argument("--model-family", default="LightGBM")
    p.add_argument("--random-state", type=int, default=42)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = run_feature_set_comparison(
        train_path=args.train,
        holdout_path=args.holdout,
        label_col=args.label_col,
        feature_sets=args.feature_set,
        output_dir=args.output_dir,
        run_name=args.run_name,
        model_family=args.model_family,
        random_state=args.random_state,
    )
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Feature set comparison completed.")
        print(f"best feature set: {rep.get('best_feature_set')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
