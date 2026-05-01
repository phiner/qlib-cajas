#!/usr/bin/env python3
"""Run Qlib workflow dry-run loader without Qlib execution or training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.qlib_compat.workflow_dry_run_loader import run_qlib_workflow_dry_run_loader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Qlib workflow dry-run loader (resolve class paths only, no execution)."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/qlib_workflow_dry_run_loader")
    parser.add_argument("--run-name", default="phase18_qlib_workflow_dry_run_loader")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_qlib_workflow_dry_run_loader(
            config_path=args.config,
            input_override=args.input_override,
        )
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = report.to_dict()

    if args.write_artifacts:
        write_baseline_reports(
            output_dir=args.output_dir,
            run_name=args.run_name,
            reports={
                "qlib_workflow_dry_run_loader_report": payload,
                "class_resolution_report": payload["class_resolution"],
                "qlib_workflow_config_draft": payload["workflow_config"],
            },
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("Qlib workflow dry-run loader completed.")
    print(f"config name: {payload['config_name']}")
    print("workflow config built: " + ("true" if payload["workflow_config_built"] else "false"))
    print("qlib available: " + ("true" if payload["qlib_available"] else "false"))
    print("qlib initialized: false")
    print("qlib workflow executed: false")
    print("training enabled: false")
    print("training executed: false")
    print("model enabled: false")
    print("model constructed: false")
    print("dataset adapter resolved: " + ("true" if payload["dataset_adapter_resolved"] else "false"))
    print("workflow bridge resolved: " + ("true" if payload["workflow_bridge_resolved"] else "false"))

    unresolved = payload["class_resolution"].get("unresolved", [])
    print("resolved classes:")
    if not unresolved:
        print("  - all declared classes resolved")
    else:
        for item in payload["class_resolution"].get("results", []):
            state = "resolved" if item["resolved"] else "unresolved"
            print(f"  - {item['dotted_path']}: {state}")

    print("blockers:")
    if payload["blockers"]:
        for blocker in payload["blockers"]:
            print(f"  - {blocker}")
    else:
        print("  - none")

    print("warnings:")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    else:
        print("  - none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
