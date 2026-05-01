#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.feature_importance_summary import summarize_feature_importance_across_runs


def main() -> int:
    p = argparse.ArgumentParser(description="Summarize feature importance across runs.")
    p.add_argument("--run-dir", action="append", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--top-k", type=int, default=50)
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = summarize_feature_importance_across_runs(run_dirs=args.run_dir, top_k=args.top_k)
    payload = rep.to_dict()

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)
        (out_dir / "feature_importance_summary_report.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pd.DataFrame([x for x in payload["features"]]).to_csv(out_dir / "feature_importance_summary.csv", index=False)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Feature importance summary completed.")
        print(f"run count: {payload['run_count']}")
        print(f"top features: {len(payload['features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
