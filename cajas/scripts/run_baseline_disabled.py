#!/usr/bin/env python3
"""Run the Phase 12 baseline command skeleton (training remains blocked)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_runner import run_training_disabled_baseline
from cajas.recorders.dry_run_recorder import DryRunRecorder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run training-disabled baseline command skeleton.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--model-family", default="LightGBM")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_disabled_runs")
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def run_baseline_disabled(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    write_artifacts: bool = False,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    report = run_training_disabled_baseline(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=False,
    )
    payload = report.to_dict()
    return write_baseline_disabled_artifacts(
        payload=payload,
        write_artifacts=write_artifacts,
        output_dir=output_dir,
        run_name=run_name,
    )


def write_baseline_disabled_artifacts(
    *,
    payload: dict,
    write_artifacts: bool,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    payload = dict(payload)
    payload["artifacts_written"] = False
    if not write_artifacts:
        return payload

    recorder = DryRunRecorder(
        output_dir=output_dir or "tmp/cajas/baseline_disabled_runs",
        run_name=run_name,
    )
    blocked = recorder.paths.run_dir / "baseline_blocked_run_report.json"
    contract = recorder.paths.run_dir / "baseline_run_contract.json"
    blocked.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contract.write_text(
        json.dumps(payload["run_contract"], ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    payload["artifacts_written"] = True
    payload["artifact_paths"] = {
        "run_dir": str(recorder.paths.run_dir),
        "baseline_blocked_run_report": str(blocked),
        "baseline_run_contract": str(contract),
    }
    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = run_baseline_disabled(
            config_path=args.config,
            input_override=args.input_override,
            model_family=args.model_family,
            write_artifacts=args.write_artifacts,
            output_dir=args.output_dir,
            run_name=args.run_name,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
            return 0

        print("Baseline disabled run completed.")
        print(f"config: {payload['config_name']}")
        print(f"phase: {payload['phase']}")
        print(f"model family: {payload['model_family']}")
        print(f"target label: {payload['target_label']}")
        print("can_train: " + ("true" if payload["can_train"] else "false"))
        print("training enabled: " + ("true" if payload["training_enabled"] else "false"))
        print(
            "phase policy allows training: "
            + ("true" if payload["phase_policy_allows_training"] else "false")
        )
        print("training executed: " + ("true" if payload["training_executed"] else "false"))
        print("model built: " + ("true" if payload["model_built"] else "false"))
        print("predictions generated: " + ("true" if payload["predictions_generated"] else "false"))
        print("evaluation executed: " + ("true" if payload["evaluation_executed"] else "false"))
        print("serialized model: " + ("true" if payload["serialized_model"] else "false"))
        print("blockers:")
        for b in payload["blockers"]:
            print(f"  - {b}")
        print("next steps:")
        for s in payload["next_steps"]:
            print(f"  - {s}")
        print("artifacts written: " + ("yes" if payload["artifacts_written"] else "no"))
        if payload["artifacts_written"]:
            print("run directory: " + payload["artifact_paths"]["run_dir"])
            print("files written:")
            print("  - baseline_blocked_run_report.json")
            print("  - baseline_run_contract.json")

        expected_blockers = {
            "Training remains disabled by Phase 10 policy.",
            "Training disabled by config (training.enabled=false).",
            "Training disabled by Phase 12 policy.",
        }
        non_expected = [b for b in payload["blockers"] if b not in expected_blockers]
        if non_expected:
            print("ERROR: non-expected blocker(s) in baseline disabled run", file=sys.stderr)
            return 1
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
