#!/usr/bin/env python3
"""Run Qlib DatasetH compatibility probe without training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.qlib_compat.dataset_shape_probe import run_dataset_h_shape_probe


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Probe Qlib DatasetH compatibility (no training). "
            "For adapter-level comparison also see probe_qlib_dataset_h_adapter.py."
        )
    )
    p.add_argument("--config", required=True)
    p.add_argument("--input-override", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--output-dir", default="tmp/cajas/qlib_compat")
    p.add_argument("--run-name", default="phase15_qlib_dataset_compat")
    p.add_argument("--require-qlib", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_dataset_h_shape_probe(config_path=args.config, input_override=args.input_override)
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()
    qlib_api = payload["qlib_dataset_api"]

    if args.write_artifacts:
        write_baseline_reports(
            output_dir=args.output_dir,
            run_name=args.run_name,
            reports={
                "qlib_dataset_compat_report": payload,
                "qlib_import_status": qlib_api,
            },
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Qlib dataset compatibility probe completed.")
        print(f"config name: {payload['config_name']}")
        print("qlib available: " + ("true" if qlib_api["qlib_available"] else "false"))
        print("DatasetH available: " + ("true" if qlib_api["dataset_h_available"] else "false"))
        print("DataHandler available: " + ("true" if qlib_api["data_handler_available"] else "false"))
        print("DataHandlerLP available: " + ("true" if qlib_api["data_handler_lp_available"] else "false"))
        print("compatible shape: " + ("yes" if payload["compatible_shape"] else "no"))
        print(f"feature count: {payload['feature_count']}")
        print("segments:")
        for seg in payload["segments"]:
            print(
                f"  - {seg['segment']}: feature_rows={seg['feature_rows']} feature_cols={seg['feature_cols']} "
                f"label_rows={seg['label_rows']} row_count_match={'yes' if seg['row_count_match'] else 'no'}"
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

    if args.require_qlib and not qlib_api["qlib_available"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
