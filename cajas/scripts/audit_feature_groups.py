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

from cajas.baseline.feature_group_audit import build_feature_group_audit


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Audit feature groups from feature column list.")
    p.add_argument("--feature-columns-json", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/feature_group_audits")
    p.add_argument("--run-name", default="phase39_feature_group_audit")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    payload_json = json.loads(Path(args.feature_columns_json).expanduser().resolve().read_text(encoding="utf-8"))
    cols = payload_json.get("feature_columns", [])
    if not isinstance(cols, list):
        print("ERROR: feature_columns must be a list", file=sys.stderr)
        return 1
    report = build_feature_group_audit([str(c) for c in cols])

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            print(f"ERROR: Refusing to overwrite existing output directory: {out_dir}", file=sys.stderr)
            return 1
        out_dir.mkdir(parents=True, exist_ok=False)
        _write_json(out_dir / "feature_group_audit_report.json", report)
        rows = []
        for group, names in report["groups"].items():
            for name in names:
                rows.append({"group": group, "feature_column": name})
        pd.DataFrame(rows).to_csv(out_dir / "feature_group_columns.csv", index=False)
        report["artifact_output_dir"] = str(out_dir)

    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print("Feature group audit completed.")
        print(f"feature count: {report['feature_count']}")
        print("groups: " + ",".join(report["groups"].keys()))
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
