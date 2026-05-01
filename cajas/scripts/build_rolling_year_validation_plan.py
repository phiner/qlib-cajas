#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.validation.rolling_year_plan import build_rolling_year_validation_plan


def main() -> int:
    p = argparse.ArgumentParser(description="Build rolling-year validation plan.")
    p.add_argument("--output-dir", default="tmp/cajas/rolling_year_validation")
    p.add_argument("--run-name", default="phase51_rolling_year_plan")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = build_rolling_year_validation_plan(output_dir=args.output_dir, run_name=args.run_name)
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Rolling year validation plan built.")
        print(f"rows: {len(rep.get('rows', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
