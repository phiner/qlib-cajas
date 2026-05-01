#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.label_decision_report import build_label_decision_report


def main() -> int:
    p = argparse.ArgumentParser(description="Build label decision report from variant comparison artifacts.")
    p.add_argument("--comparison-report", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/label_decision_reports")
    p.add_argument("--run-name", default="phase45_label_decision_report")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = build_label_decision_report(
        comparison_report_path=args.comparison_report,
        output_dir=args.output_dir,
        run_name=args.run_name,
    )
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Label decision report completed.")
        print(f"output dir: {rep['output_dir']}")
        print(f"recommendation: {rep['recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
