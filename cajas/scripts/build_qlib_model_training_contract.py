#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_model_training_contract_builder import build_qlib_model_training_contract


def main() -> int:
    p = argparse.ArgumentParser(description="Build qlib model bridge training contract.")
    p.add_argument("--handler-input", required=True)
    p.add_argument("--handler-manifest", required=True)
    p.add_argument("--dataset-contract", required=True)
    p.add_argument("--handler-smoke-report", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--run-id", default="phase086_model_bridge")
    p.add_argument("--label-col", default=None)
    p.add_argument("--row-limit", type=int, default=None)
    p.add_argument("--allow-large-data", action="store_true")
    args = p.parse_args()

    contract = build_qlib_model_training_contract(
        handler_input_path=args.handler_input,
        handler_manifest_path=args.handler_manifest,
        dataset_contract_path=args.dataset_contract,
        handler_smoke_report_path=args.handler_smoke_report,
        out_path=args.out,
        run_id=args.run_id,
        label_col=args.label_col,
        row_limit=args.row_limit,
        allow_large_data=args.allow_large_data,
    )
    print("Qlib model training contract completed.")
    print(f"output: {Path(args.out).expanduser().resolve()}")
    print(f"readiness_status: {contract['readiness_status']}")
    return 0 if contract["readiness_status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
