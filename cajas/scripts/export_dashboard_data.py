#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.dashboard_export import export_dashboard_data


def main() -> int:
    p = argparse.ArgumentParser(description="Export dashboard-ready data artifacts.")
    p.add_argument("--registry", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--baseline-run-dir", action="append", dest="baseline_run_dirs")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = export_dashboard_data(
        registry_path=args.registry,
        output_dir=args.output_dir,
        run_name=args.run_name,
        baseline_run_dirs=args.baseline_run_dirs,
    )
    payload = rep.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Dashboard export completed.")
        print(f"run count: {payload['run_count']}")
        print(f"files written: {len(payload['files_written'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
