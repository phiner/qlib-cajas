#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_readiness_report import build_qlib_readiness_report


def main() -> int:
    p = argparse.ArgumentParser(description="Build phase-54 Qlib integration readiness report.")
    p.add_argument("--output-dir", default="tmp/cajas/qlib_readiness_reports")
    p.add_argument("--run-name", default="phase54_qlib_readiness_report")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = build_qlib_readiness_report(output_dir=args.output_dir, run_name=args.run_name)
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Qlib readiness report completed.")
        print(f"output dir: {rep.get('output_dir')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
