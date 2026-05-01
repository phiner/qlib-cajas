#!/usr/bin/env python3
"""Build a training-disabled baseline plan report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_plan import build_baseline_plan
from cajas.recorders.dry_run_recorder import DryRunRecorder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build training-disabled baseline plan.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--model-family", default="LightGBM")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_plans")
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def run_baseline_plan(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    strict: bool = False,
    write_artifacts: bool = False,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    report = build_baseline_plan(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        strict=strict,
    )
    payload = report.to_dict()
    payload["artifacts_written"] = False

    if write_artifacts:
        recorder = DryRunRecorder(
            output_dir=output_dir or "tmp/cajas/baseline_plans", run_name=run_name
        )
        out = recorder.paths.run_dir / "baseline_plan_report.json"
        out.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["artifacts_written"] = True
        payload["artifact_paths"] = {
            "run_dir": str(recorder.paths.run_dir),
            "baseline_plan_report": str(out),
        }
    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = run_baseline_plan(
            config_path=args.config,
            input_override=args.input_override,
            model_family=args.model_family,
            strict=args.strict,
            write_artifacts=args.write_artifacts,
            output_dir=args.output_dir,
            run_name=args.run_name,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
            return 0

        print("Baseline plan completed.")
        print(f"config: {payload['config_name']}")
        print(f"model family: {payload['model_spec']['model_family']}")
        print(f"target label: {payload['model_spec']['target_label']}")
        print(f"task type: {payload['model_spec']['task_type']}")
        print("ready non-strict: " + ("yes" if payload["ready_non_strict"] else "no"))
        print("ready strict: " + ("yes" if payload["ready_strict"] else "no"))
        print("training enabled: " + ("true" if payload["training_enabled"] else "false"))
        print("training allowed: " + ("true" if payload["training_allowed"] else "false"))
        print("training executed: " + ("true" if payload["training_executed"] else "false"))
        missing = [d["name"] for d in payload["dependency_probe"]["dependencies"] if not d["available"]]
        print("dependency missing: " + (", ".join(missing) if missing else "none"))
        print("blockers:")
        for b in payload["blockers"]:
            print(f"  - {b}")
        print("warnings:")
        for w in payload["warnings"]:
            print(f"  - {w}")
        print("artifacts written: " + ("yes" if payload["artifacts_written"] else "no"))
        if payload["artifacts_written"]:
            print("run directory: " + payload["artifact_paths"]["run_dir"])
            print("files written:")
            print("  - baseline_plan_report.json")
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
