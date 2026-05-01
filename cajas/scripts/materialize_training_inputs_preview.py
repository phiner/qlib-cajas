#!/usr/bin/env python3
"""Materialize Phase 14 training input preview artifacts without training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.training_input_materialization import materialize_training_inputs_preview


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize training input preview artifacts for Phase 14 (no training)."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default="tmp/cajas/training_input_previews")
    parser.add_argument("--run-name", default="phase14_training_inputs_preview")
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--no-csv", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = materialize_training_inputs_preview(
            config_path=args.config,
            output_dir=args.output_dir,
            run_name=args.run_name,
            input_override=args.input_override,
            write_csv=not args.no_csv,
        )
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("Training input materialization preview completed.")
    print(f"config name: {payload['config_name']}")
    print(f"label column: {payload['label_col']}")
    print(f"feature count: {payload['feature_count']}")
    print("label encoding mapping: " + json.dumps(payload["label_encoding"]["mapping"], sort_keys=True))
    print(f"primary metric: {payload['metric_plan']['primary_metric']}")
    print("segments:")
    for segment in payload["segments"]:
        print(
            f"  - {segment['segment']}: feature_rows={segment['feature_rows']} "
            f"feature_cols={segment['feature_cols']} label_rows={segment['label_rows']} "
            f"encoded_label_rows={segment['encoded_label_rows']}"
        )
        files = segment["output_files"]
        if files:
            for _, path in files.items():
                print(f"      file: {path}")
    print("training enabled: " + ("true" if payload["training_enabled"] else "false"))
    print("training executed: " + ("true" if payload["training_executed"] else "false"))
    print("model built: " + ("true" if payload["model_built"] else "false"))
    print("always-written files:")
    print(f"  - {args.output_dir}/{args.run_name}/training_input_materialization_report.json")
    print(f"  - {args.output_dir}/{args.run_name}/label_encoding_preview.json")
    print(f"  - {args.output_dir}/{args.run_name}/metric_plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
