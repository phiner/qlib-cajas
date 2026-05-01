#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.external_holdout_benchmark import build_external_holdout_benchmark


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Benchmark internal split vs external holdout runs.")
    p.add_argument("--run-dir", action="append", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/external_holdout_benchmarks")
    p.add_argument("--run-name", default="phase36_external_holdout_benchmark")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = build_external_holdout_benchmark(run_dirs=args.run_dir)
    payload = report.to_dict()

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            print(f"ERROR: Refusing to overwrite existing output directory: {out_dir}", file=sys.stderr)
            return 1
        out_dir.mkdir(parents=True, exist_ok=False)
        _write_json(out_dir / "external_holdout_benchmark_report.json", payload)
        rows = [s for s in payload["summaries"]]
        pd.DataFrame(rows).to_csv(out_dir / "external_holdout_benchmark.csv", index=False)
        payload["artifact_output_dir"] = str(out_dir)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("External holdout benchmark completed.")
        print(f"run count: {payload['run_count']}")
        print(f"internal split runs: {payload['internal_split_count']}")
        print(f"external holdout runs: {payload['external_holdout_count']}")
        print(f"best external holdout by macro_f1: {payload['best_external_holdout_by_macro_f1']}")
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
