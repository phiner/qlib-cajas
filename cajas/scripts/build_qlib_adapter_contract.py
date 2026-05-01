#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_adapter_contract_builder import build_qlib_adapter_contract


def main() -> int:
    p = argparse.ArgumentParser(description="Build Qlib adapter contract from promotion manifest.")
    p.add_argument("--promotion-manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--dataset-version", default="eurusd_15m_v1")
    p.add_argument("--feature-set-id", required=True)
    p.add_argument("--label-variant-id", required=True)
    p.add_argument("--target-name", required=True)
    p.add_argument("--frequency", required=True)
    p.add_argument("--prediction-horizon", type=int, default=8)
    p.add_argument("--strict-paths", action="store_true")
    args = p.parse_args()

    contract, issues = build_qlib_adapter_contract(
        promotion_manifest_path=args.promotion_manifest,
        candidate_id=args.candidate_id,
        dataset_version=args.dataset_version,
        feature_set_id=args.feature_set_id,
        label_variant_id=args.label_variant_id,
        target_name=args.target_name,
        frequency=args.frequency,
        prediction_horizon=args.prediction_horizon,
        strict_paths=args.strict_paths,
    )

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(contract, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "issue_count": len(issues),
        "error_count": sum(1 for i in issues if i.severity == "error"),
        "warning_count": sum(1 for i in issues if i.severity == "warning"),
        "issues": [i.to_dict() for i in issues],
    }
    (out.parent / f"{out.stem}.validation.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("Qlib adapter contract completed.")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
