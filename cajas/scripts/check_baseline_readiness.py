#!/usr/bin/env python3
"""Run baseline readiness check without enabling any model training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.readiness.baseline_readiness import run_baseline_readiness_check
from cajas.recorders.dry_run_recorder import DryRunRecorder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check baseline readiness gate.")
    parser.add_argument("--config", required=True, help="YAML config path")
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_readiness")
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def run_readiness(
    *,
    config_path: str,
    input_override: str | None = None,
    strict: bool = False,
    write_artifacts: bool = False,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    report = run_baseline_readiness_check(
        config_path=config_path,
        input_override=input_override,
        strict=strict,
    )
    payload = report.to_dict()
    payload["artifacts_written"] = False

    if write_artifacts:
        recorder = DryRunRecorder(
            output_dir=output_dir or "tmp/cajas/baseline_readiness",
            run_name=run_name,
        )
        out_path = recorder.paths.run_dir / "baseline_readiness_report.json"
        out_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["artifacts_written"] = True
        payload["artifact_paths"] = {
            "run_dir": str(recorder.paths.run_dir),
            "baseline_readiness_report": str(out_path),
        }

    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = run_readiness(
            config_path=args.config,
            input_override=args.input_override,
            strict=args.strict,
            write_artifacts=args.write_artifacts,
            output_dir=args.output_dir,
            run_name=args.run_name,
        )
        has_error = any(i.get("severity") == "error" for i in payload["issues"])
        if args.strict and not payload["ready"]:
            print("ERROR: readiness check failed in strict mode", file=sys.stderr)
            return 1
        if has_error:
            print("ERROR: readiness check has error-severity issues", file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
            return 0

        print("Baseline readiness check completed.")
        print(f"config: {payload['config_name']}")
        print("ready: " + ("yes" if payload["ready"] else "no"))
        print(
            "training enabled: "
            + ("yes" if payload["training_enabled"] else "no")
        )
        print(
            "training executed: "
            + ("yes" if payload["training_executed"] else "no")
        )
        print(f"feature count: {payload['feature_count']}")
        print("segments:")
        for name, stats in payload["segments"].items():
            print(
                f"  {name}: features={stats['feature_rows']}, labels={stats['label_rows']}"
            )
        print(
            f"feature audit issues: {len(payload['feature_audit']['issues'])}"
        )
        print(f"label audit issues: {len(payload['label_audit']['issues'])}")
        print("artifacts written: " + ("yes" if payload["artifacts_written"] else "no"))
        if payload["artifacts_written"]:
            print("run directory: " + payload["artifact_paths"]["run_dir"])
            print("files written:")
            print("  - baseline_readiness_report.json")
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
