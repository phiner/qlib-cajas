#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_report_pack import build_research_report_pack


def main() -> int:
    p = argparse.ArgumentParser(description="Build consolidated research report pack from existing artifacts.")
    p.add_argument("--registry", required=True)
    p.add_argument("--baseline-run-dir", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = build_research_report_pack(
        output_dir=args.output_dir,
        run_name=args.run_name,
        title=args.title,
        registry_path=args.registry,
        baseline_run_dir=args.baseline_run_dir,
        include_dashboard_export=True,
    )
    payload = rep.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Research report pack completed.")
        print(f"output dir: {payload['output_dir']}")
        print("no trading/backtest/profit sections included")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
