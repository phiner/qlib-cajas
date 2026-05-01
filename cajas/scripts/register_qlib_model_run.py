#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_model_run_registry import register_qlib_model_run


def main() -> int:
    p = argparse.ArgumentParser(description="Register qlib model bridge experiment run.")
    p.add_argument("--experiment-dir", required=True)
    p.add_argument("--registry", required=True)
    args = p.parse_args()

    exp = Path(args.experiment_dir).expanduser().resolve()
    manifest = json.loads((exp / "experiment_manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8"))
    split_summary = json.loads((exp / "split_summary.json").read_text(encoding="utf-8"))
    feature_columns = json.loads((exp / "feature_columns.json").read_text(encoding="utf-8"))

    record = {
        "run_id": manifest.get("run_id", "unknown"),
        "timestamp": manifest.get("timestamp", ""),
        "feature_count": len(feature_columns.get("feature_columns", [])),
        "row_counts": split_summary,
        "metrics": {
            "accuracy": metrics.get("valid", {}).get("accuracy"),
            "macro_f1": metrics.get("valid", {}).get("macro_f1"),
        },
        "artifact_paths": {"experiment_dir": str(exp)},
        "status": "ok",
        "warnings": [],
    }
    rep = register_qlib_model_run(registry_path=args.registry, record=record)
    print("Qlib model run registered.")
    print(f"registry: {rep['registry_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
