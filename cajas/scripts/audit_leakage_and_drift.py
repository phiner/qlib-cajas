#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.audits.leakage_drift_audit import run_leakage_drift_audit


def main() -> int:
    p = argparse.ArgumentParser(description="Audit leakage and train/holdout drift.")
    p.add_argument("--train", required=True)
    p.add_argument("--holdout", required=True)
    p.add_argument("--feature-columns-json", required=True)
    p.add_argument("--label-col", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/leakage_drift_audits")
    p.add_argument("--run-name", default="phase53_leakage_drift_audit")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = run_leakage_drift_audit(
        train_path=args.train,
        holdout_path=args.holdout,
        feature_columns_path=args.feature_columns_json,
        label_col=args.label_col,
        output_dir=args.output_dir,
        run_name=args.run_name,
    )
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Leakage/drift audit completed.")
        print(f"forbidden feature columns: {len(rep.get('forbidden_feature_columns', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
