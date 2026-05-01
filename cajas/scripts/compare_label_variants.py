#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.label_variant_comparison import compare_label_variant_runs, write_label_variant_comparison_artifacts


def main() -> int:
    p = argparse.ArgumentParser(description="Compare label-variant external holdout runs.")
    p.add_argument("--run-dir", action="append", required=True)
    p.add_argument("--primary-metric", default="macro_f1")
    p.add_argument("--output-dir", default="tmp/cajas/label_variant_comparisons")
    p.add_argument("--run-name", default="phase44_label_variant_comparison")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = compare_label_variant_runs(run_dirs=args.run_dir, primary_metric=args.primary_metric)
    if args.write_artifacts:
        out = Path(args.output_dir).expanduser().resolve() / args.run_name
        out.mkdir(parents=True, exist_ok=False)
        write_label_variant_comparison_artifacts(report=rep, output_dir=out)
        rep["artifact_output_dir"] = str(out)
    if args.json:
        print(json.dumps(rep, ensure_ascii=True, indent=2))
    else:
        print("Label variant comparison completed.")
        print(f"run count: {rep['run_count']}")
        print(f"best run: {rep['best_run']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
