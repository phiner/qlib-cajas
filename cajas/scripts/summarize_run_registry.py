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

from cajas.registry.registry_reports import build_run_registry_summary


def main() -> int:
    p = argparse.ArgumentParser(description="Summarize local run registry.")
    p.add_argument("--registry", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = build_run_registry_summary(registry_path=args.registry)
    payload = rep.to_dict()

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)
        (out_dir / "run_registry_summary_report.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pd.DataFrame(payload["training_runs"]).to_csv(out_dir / "run_registry_summary.csv", index=False)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Run registry summary completed.")
        print(f"total records: {payload['total_records']}")
        print(f"training runs: {len(payload['training_runs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
