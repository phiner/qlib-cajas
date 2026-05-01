#!/usr/bin/env python3
"""Run training-disabled experiment plan dry-run from YAML config."""

from __future__ import annotations

import argparse
from dataclasses import asdict
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
from cajas.recorders.dry_run_recorder import DryRunRecorder
from cajas.workflows.prepared_workflow import PreparedWorkflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate config and run PreparedWorkflow dry-run plan."
    )
    parser.add_argument("--config", required=True, help="YAML config path")
    parser.add_argument("--input-override", default=None, help="Optional CSV override path")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    parser.add_argument("--output-dir", default="tmp/cajas/experiment_dry_runs")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when validation issues exist",
    )
    return parser.parse_args()


def run_experiment_plan(
    config_path: str,
    input_override: str | None = None,
    output_dir: str | None = None,
    run_name: str | None = None,
    write_artifacts: bool = False,
    strict: bool = False,
) -> tuple[dict, list[str]]:
    config = load_experiment_config(config_path)
    issues = validate_experiment_config(config)
    assert_training_disabled(config)
    if strict and issues:
        raise ValueError("strict mode failed due to validation issues")

    wf_config = build_workflow_config(config, csv_path_override=input_override)
    workflow_summary = PreparedWorkflow(wf_config).dry_run()
    segment_shapes = [asdict(s) for s in workflow_summary.segment_shapes]

    validation_report = {
        "issues": issues,
        "strict_mode": strict,
        "leakage_columns_declared": list(config.data_adapter.leakage_columns),
        "leakage_columns_found_in_features": workflow_summary.leakage_columns_in_features,
        "training_disabled_check": "pass",
        "dry_run_only_check": "pass" if config.workflow_bridge.dry_run_only else "fail",
    }

    payload = {
        "config": config.name,
        "csv": wf_config.csv_path,
        "label": workflow_summary.label_col,
        "training_enabled": config.training.enabled,
        "workflow_dry_run_only": config.workflow_bridge.dry_run_only,
        "feature_columns": workflow_summary.feature_columns,
        "feature_count": len(workflow_summary.feature_columns),
        "segment_shapes": segment_shapes,
        "leakage_columns_in_features": workflow_summary.leakage_columns_in_features,
        "training_executed": workflow_summary.training_executed,
        "issues": issues,
    }

    if write_artifacts:
        recorder = DryRunRecorder(output_dir=output_dir or "tmp/cajas/experiment_dry_runs", run_name=run_name)
        manifest = {
            "run_name": recorder.paths.run_dir.name,
            "run_type": "experiment_plan_dry_run",
            "config_name": config.name,
            "label_col": config.data_adapter.label_col,
            "training_enabled": config.training.enabled,
            "training_executed": workflow_summary.training_executed,
            "qlib_core_modified": False,
            "created_by": "cajas/scripts/run_experiment_plan_dry_run.py",
        }
        config_snapshot = {
            "name": config.name,
            "csv_path": config.data_adapter.csv_path,
            "label_col": config.data_adapter.label_col,
            "leakage_columns": list(config.data_adapter.leakage_columns),
            "segments": {
                key: {"start": value.start, "end": value.end}
                for key, value in config.data_adapter.segments.items()
            },
            "handler_class": config.data_adapter.handler_class,
            "dataset_class": config.data_adapter.dataset_class,
            "workflow_class": config.workflow_bridge.workflow_class,
            "dry_run_only": config.workflow_bridge.dry_run_only,
            "training_enabled": config.training.enabled,
        }
        recorder.write_all(
            manifest=manifest,
            config_snapshot=config_snapshot,
            workflow_summary=workflow_summary.to_dict(),
            validation_report=validation_report,
        )
        payload["artifacts_written"] = True
        payload["artifact_paths"] = {
            "run_dir": str(recorder.paths.run_dir),
            "run_manifest": str(recorder.paths.manifest_path),
            "config_snapshot": str(recorder.paths.config_snapshot_path),
            "workflow_summary": str(recorder.paths.workflow_summary_path),
            "validation_report": str(recorder.paths.validation_report_path),
        }
    else:
        payload["artifacts_written"] = False

    return payload, issues


def main() -> int:
    args = parse_args()
    try:
        payload, issues = run_experiment_plan(
            config_path=args.config,
            input_override=args.input_override,
            output_dir=args.output_dir,
            run_name=args.run_name,
            write_artifacts=args.write_artifacts,
            strict=args.strict,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
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
        print("artifacts written: " + ("yes" if payload["artifacts_written"] else "no"))
        if payload["artifacts_written"]:
            print("run directory: " + payload["artifact_paths"]["run_dir"])
            print("files written:")
            print("  - run_manifest.json")
            print("  - config_snapshot.json")
            print("  - workflow_summary.json")
            print("  - validation_report.json")
        if issues:
            print("issues:")
            for issue in issues:
                print(f"- {issue}")
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
