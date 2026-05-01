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

from cajas.registry.run_health_check import check_run_registry_health


def main() -> int:
    p = argparse.ArgumentParser(description="Check health of local run registry/artifacts.")
    p.add_argument("--registry", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = check_run_registry_health(registry_path=args.registry)
    payload = report.to_dict()

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)
        (out_dir / "run_health_report.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pd.DataFrame([x for x in payload["issues"]]).to_csv(out_dir / "run_health_issues.csv", index=False)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Run health check completed.")
        print(f"checked runs: {payload['checked_runs']}")
        print(f"healthy runs: {payload['healthy_runs']}")
        print(f"warnings: {payload['warning_count']}")
        print(f"errors: {payload['error_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
