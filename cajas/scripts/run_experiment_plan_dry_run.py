#!/usr/bin/env python3
"""Run training-disabled experiment plan dry-run from YAML config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.config.experiment_config import (
    assert_training_disabled,
    build_workflow_config,
    load_experiment_config,
    validate_experiment_config,
)
from cajas.workflows.prepared_workflow import PreparedWorkflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate config and run PreparedWorkflow dry-run plan."
    )
    parser.add_argument("--config", required=True, help="YAML config path")
    parser.add_argument("--input-override", default=None, help="Optional CSV override path")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when validation issues exist",
    )
    return parser.parse_args()


def run_experiment_plan(
    config_path: str,
    input_override: str | None = None,
) -> tuple[dict, list[str]]:
    config = load_experiment_config(config_path)
    issues = validate_experiment_config(config)
    assert_training_disabled(config)

    wf_config = build_workflow_config(config, csv_path_override=input_override)
    summary = PreparedWorkflow(wf_config).dry_run()
    payload = {
        "config": config.name,
        "csv": wf_config.csv_path,
        "label": summary.label_col,
        "training_enabled": config.training.enabled,
        "workflow_dry_run_only": config.workflow_bridge.dry_run_only,
        "feature_count": len(summary.feature_columns),
        "segment_shapes": [s.__dict__ for s in summary.segment_shapes],
        "leakage_columns_in_features": summary.leakage_columns_in_features,
        "training_executed": summary.training_executed,
    }
    return payload, issues


def main() -> int:
    args = parse_args()
    try:
        payload, issues = run_experiment_plan(
            config_path=args.config,
            input_override=args.input_override,
        )
        if args.strict and issues:
            print("ERROR: strict mode failed due to validation issues", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            return 1

        if args.json:
            payload_json = dict(payload)
            payload_json["issues"] = issues
            print(json.dumps(payload_json, ensure_ascii=True, indent=2))
            return 0

        print("Experiment plan dry-run completed.")
        print(f"config: {payload['config']}")
        print(f"csv: {payload['csv']}")
        print(f"label: {payload['label']}")
        print(f"training enabled: {str(payload['training_enabled']).lower()}")
        print(
            "workflow dry-run only: "
            + str(payload["workflow_dry_run_only"]).lower()
        )
        print(f"feature count: {payload['feature_count']}")
        print("segments:")
        for shape in payload["segment_shapes"]:
            print(
                f"  {shape['segment']}: features=({shape['feature_rows']}, "
                f"{shape['feature_cols']}), labels={shape['label_rows']}"
            )
        print(
            "leakage columns in features: "
            + ("yes" if payload["leakage_columns_in_features"] else "no")
        )
        print(
            "training executed: "
            + ("yes" if payload["training_executed"] else "no")
        )
        if issues:
            print("issues:")
            for issue in issues:
                print(f"- {issue}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
