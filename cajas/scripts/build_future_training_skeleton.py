#!/usr/bin/env python3
"""Build Phase 13 future baseline training skeleton report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifacts import write_baseline_reports
from cajas.baseline.future_training_skeleton import build_future_training_skeleton


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build future baseline training skeleton report.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--model-family", default="LightGBM")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/future_training_skeletons")
    parser.add_argument("--run-name", default="phase13_future_training_skeleton")
    return parser.parse_args()


def run_future_training_skeleton(
    *,
    config_path: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    write_artifacts: bool = False,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    report = build_future_training_skeleton(
        config_path=config_path,
        input_override=input_override,
        model_family=model_family,
        user_training_approval=False,
        phase_policy_allows_training=False,
    )
    payload = report.to_dict()
    payload["artifacts_written"] = False
    if write_artifacts:
        report_paths = write_baseline_reports(
            output_dir=output_dir or "tmp/cajas/future_training_skeletons",
            run_name=run_name or "phase13_future_training_skeleton",
            reports={
                "future_training_skeleton_report": payload,
                "training_enable_contract": payload["enable_contract"],
            },
        )
        payload["artifacts_written"] = True
        payload["artifact_paths"] = report_paths
    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = run_future_training_skeleton(
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

        print("Future training skeleton completed.")
        print(f"config: {payload['config_name']}")
        print(f"phase: {payload['phase']}")
        print(f"model family: {payload['model_family']}")
        print(f"target label: {payload['target_label']}")
        print("can enable training: " + ("true" if payload["can_enable_training"] else "false"))
        print("can train now: " + ("true" if payload["can_train_now"] else "false"))
        print("training executed: " + ("true" if payload["training_executed"] else "false"))
        print("model built: " + ("true" if payload["model_built"] else "false"))
        print("fit executed: " + ("true" if payload["fit_executed"] else "false"))
        print("prediction executed: " + ("true" if payload["prediction_executed"] else "false"))
        print("evaluation executed: " + ("true" if payload["evaluation_executed"] else "false"))
        print("serialization executed: " + ("true" if payload["serialization_executed"] else "false"))
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
            print("  - future_training_skeleton_report.json")
            print("  - training_enable_contract.json")

        expected_blockers = {
            "Training remains disabled by Phase 10 policy.",
            "Training disabled by config (training.enabled=false).",
            "Training disabled by Phase 12 policy.",
            "Training disabled by Phase 13 policy.",
            "Training disabled because user approval was not granted.",
        }
        non_expected = [
            b
            for b in payload["blockers"]
            if not (b in expected_blockers or b.startswith("Required gate disabled:"))
        ]
        if non_expected:
            print("ERROR: non-expected blocker(s) in future training skeleton", file=sys.stderr)
            return 1
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
