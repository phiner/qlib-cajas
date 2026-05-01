#!/usr/bin/env python3
"""Probe Qlib-style workflow config shape without execution or training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.qlib_compat.workflow_config_probe import probe_qlib_workflow_config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe Qlib workflow config shape (no qlib init, no training).")
    p.add_argument("--config", required=True)
    p.add_argument("--input-override", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--output-dir", default="tmp/cajas/qlib_workflow_config")
    p.add_argument("--run-name", default="phase17_qlib_workflow_config")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = probe_qlib_workflow_config(config_path=args.config, input_override=args.input_override)
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()

    if args.write_artifacts:
        write_baseline_reports(
            output_dir=args.output_dir,
            run_name=args.run_name,
            reports={
                "qlib_workflow_config_probe_report": payload,
                "qlib_workflow_config_draft": payload["workflow_config"],
            },
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("Qlib workflow config probe completed.")
    print(f"config name: {payload['config_name']}")
    print("qlib available: " + ("true" if payload["qlib_available"] else "false"))
    print("workflow config built: " + ("true" if payload["workflow_config_built"] else "false"))
    print("training enabled: false")
    print("training executed: false")
    print("qlib initialized: false")
    print("qlib workflow executed: false")
    print("dataset class: " + payload["workflow_config"]["dataset"]["class"])
    print("model family: " + payload["workflow_config"]["model"]["family"])
    print("feature count: " + str(payload["workflow_config"]["dataset"]["feature_count"]))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
