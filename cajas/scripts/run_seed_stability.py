#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.seed_stability import run_seed_stability_experiment


def main() -> int:
    p = argparse.ArgumentParser(description="Run seed stability experiment for external holdout.")
    p.add_argument("--train", required=True)
    p.add_argument("--holdout", required=True)
    p.add_argument("--label-col", required=True)
    p.add_argument("--seed", action="append", type=int, required=True)
    p.add_argument("--output-dir", default="tmp/cajas/seed_stability")
    p.add_argument("--run-name", default="phase50_seed_stability")
    p.add_argument("--model-family", default="LightGBM")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = run_seed_stability_experiment(
        train_path=args.train,
        holdout_path=args.holdout,
        label_col=args.label_col,
        output_dir=args.output_dir,
        run_name=args.run_name,
        seeds=args.seed,
        model_family=args.model_family,
    )
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Seed stability experiment completed.")
        print(f"macro_f1_mean: {rep.get('macro_f1_mean')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
