#!/usr/bin/env python3
"""Probe real Qlib DatasetH adapter compatibility without training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.qlib_compat.adapter_comparison_probe import run_adapter_comparison_probe
from cajas.qlib_compat.prepared_dataset_h_adapter import PreparedQlibDatasetHAdapter


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe Qlib DatasetH adapter compatibility (no training).")
    p.add_argument("--config", required=True)
    p.add_argument("--input-override", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument("--require-qlib", action="store_true")
    p.add_argument("--require-true-subclass", action="store_true")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--output-dir", default="tmp/cajas/qlib_adapter")
    p.add_argument("--run-name", default="phase16_qlib_dataset_h_adapter")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_adapter_comparison_probe(config_path=args.config, input_override=args.input_override)

        cfg = load_experiment_config(args.config)
        wf_cfg = build_workflow_config(cfg, csv_path_override=args.input_override)
        prepared = PreparedDataset(wf_cfg.csv_path, wf_cfg.label_col, wf_cfg.segments)
        adapter = PreparedQlibDatasetHAdapter(prepared)
        adapter_desc = adapter.describe()
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()

    if args.write_artifacts:
        write_baseline_reports(
            output_dir=args.output_dir,
            run_name=args.run_name,
            reports={
                "qlib_dataset_h_adapter_report": payload,
                "qlib_dataset_h_adapter_description": adapter_desc,
            },
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Qlib DatasetH adapter probe completed.")
        print(f"config name: {payload['config_name']}")
        print("qlib available: " + ("true" if payload["qlib_available"] else "false"))
        print(
            "adapter constructed: "
            + ("true" if payload["qlib_adapter_constructed"] else "false")
        )
        print(
            "true Qlib subclass: "
            + ("yes" if payload["qlib_adapter_true_subclass"] else "no")
        )
        print("compatible: " + ("yes" if payload["compatible"] else "no"))
        print(f"feature count: {payload['feature_count']}")
        print("segments:")
        for seg in payload["segments"]:
            print(
                f"  - {seg['segment']}: prepared_rows={seg['prepared_rows']} "
                f"h_like_rows={seg['h_like_rows']} qlib_adapter_rows={seg['qlib_adapter_rows']} "
                f"feature_shape_match={'yes' if seg['feature_shape_match'] else 'no'} "
                f"label_values_match={'yes' if seg['label_values_match'] else 'no'}"
            )
        print("blockers:")
        if payload["blockers"]:
            for b in payload["blockers"]:
                print(f"  - {b}")
        else:
            print("  - none")
        print("warnings:")
        if payload["warnings"]:
            for w in payload["warnings"]:
                print(f"  - {w}")
        else:
            print("  - none")
        print("training executed: false")

    if args.require_qlib and not payload["qlib_available"]:
        return 1
    if args.require_true_subclass and not payload["qlib_adapter_true_subclass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
