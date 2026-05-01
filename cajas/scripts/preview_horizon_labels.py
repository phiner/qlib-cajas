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

from cajas.datasets.horizon_label_preview import preview_horizon_labels


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Preview horizon label distributions.")
    p.add_argument("--input", required=True)
    p.add_argument("--input-name", default="")
    p.add_argument("--horizon", action="append", required=True, type=int)
    p.add_argument("--output-dir", default="tmp/cajas/horizon_label_previews")
    p.add_argument("--run-name", default="phase38_horizon_preview")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = preview_horizon_labels(input_path=args.input, horizons=args.horizon)
    payload = report.to_dict()
    if args.input_name:
        payload["input_name"] = args.input_name

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            print(f"ERROR: Refusing to overwrite existing output directory: {out_dir}", file=sys.stderr)
            return 1
        out_dir.mkdir(parents=True, exist_ok=False)
        _write_json(out_dir / "horizon_label_preview_report.json", payload)
        rows = []
        for h in payload["horizons"]:
            row = {"horizon": h["horizon"], "label_col": h["label_col"], "row_count": h["row_count"], "flat_ratio": h["flat_ratio"]}
            for label, count in h["distribution"].items():
                row[f"count_{label}"] = count
            rows.append(row)
        pd.DataFrame(rows).to_csv(out_dir / "horizon_label_distribution.csv", index=False)
        payload["artifact_output_dir"] = str(out_dir)

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Horizon label preview completed.")
        print(f"input: {payload['input_path']}")
        print("horizons: " + ",".join(str(h["horizon"]) for h in payload["horizons"]))
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
