#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.qlib_model_bridge_trainer import train_qlib_model_bridge_baseline
from cajas.reports.qlib_experiment_artifacts import write_experiment_artifacts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train CPU baseline for qlib model experiment bridge.")
    p.add_argument("--training-contract", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-rows", type=int, default=5000)
    p.add_argument("--row-limit", type=int, default=None)
    p.add_argument("--sample-only", action="store_true")
    p.add_argument("--allow-large-data", action="store_true")
    p.add_argument("--selected-columns", default=None, help="comma-separated column list")
    p.add_argument("--use-cache", action="store_true")
    p.add_argument("--manifest", default=None)
    args = p.parse_args(argv)

    contract = json.loads(Path(args.training_contract).expanduser().read_text(encoding="utf-8"))
    result = train_qlib_model_bridge_baseline(
        contract=contract,
        out_dir=args.out_dir,
        seed=args.seed,
        max_rows=args.max_rows,
        row_limit=args.row_limit,
        sample_only=args.sample_only,
        allow_large_data=args.allow_large_data,
        selected_columns=[c.strip() for c in args.selected_columns.split(",") if c.strip()] if args.selected_columns else None,
        use_cache=args.use_cache,
        manifest=args.manifest,
    )

    out = Path(args.out_dir).expanduser().resolve()
    artifacts = {
        "experiment_manifest.json": {
            "run_id": contract["run_id"],
            "model_family": result["model_family"],
            "seed": result["seed"],
            "scope": "research_only",
        },
        "train_config.json": {"seed": args.seed, "max_rows": args.max_rows},
        "metrics.json": {"valid": result["metrics_valid"], "test": result["metrics_test"]},
        "feature_columns.json": {"feature_columns": result["feature_columns"]},
        "label_distribution.json": {
            "valid_true": result["metrics_valid"]["label_distribution_true"],
            "test_true": result["metrics_test"]["label_distribution_true"],
        },
        "split_summary.json": result["split_summary"],
        "model_card.json": {
            "model_family": result["model_family"],
            "target": result["label_col"],
            "research_only": True,
            "trading_use_forbidden": True,
        },
    }
    paths = write_experiment_artifacts(out_dir=out, artifacts=artifacts)
    if Path(result["predictions_path"]).resolve() != (out / "predictions.csv"):
        pass
    print("Qlib model bridge baseline training completed.")
    print(f"output dir: {out}")
    print(f"metrics path: {paths['metrics.json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
