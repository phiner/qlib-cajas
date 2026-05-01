#!/usr/bin/env python3
"""Run Phase 11 baseline preflight gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_preflight import run_baseline_preflight
from cajas.recorders.dry_run_recorder import DryRunRecorder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline preflight gate.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--input-override", default=None)
    parser.add_argument("--model-family", default="LightGBM")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_preflight")
    parser.add_argument("--run-name", default=None)
    return parser.parse_args()


def run_preflight(
    *,
    config_path: str,
    root: str = ".",
    input_override: str | None = None,
    model_family: str = "LightGBM",
    write_artifacts: bool = False,
    output_dir: str | None = None,
    run_name: str | None = None,
) -> dict:
    report = run_baseline_preflight(
        config_path=config_path,
        root=root,
        input_override=input_override,
        model_family=model_family,
        phase_policy_allows_training=False,
    )
    payload = report.to_dict()
    payload["artifacts_written"] = False
    if write_artifacts:
        recorder = DryRunRecorder(
            output_dir=output_dir or "tmp/cajas/baseline_preflight",
            run_name=run_name,
        )
        preflight = recorder.paths.run_dir / "baseline_preflight_report.json"
        contract = recorder.paths.run_dir / "baseline_execution_contract.json"
        preflight.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        contract.write_text(
            json.dumps(payload["execution_contract"], ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["artifacts_written"] = True
        payload["artifact_paths"] = {
            "run_dir": str(recorder.paths.run_dir),
            "baseline_preflight_report": str(preflight),
            "baseline_execution_contract": str(contract),
        }
    return payload


def main() -> int:
    args = parse_args()
    try:
        payload = run_preflight(
            config_path=args.config,
            root=args.root,
            input_override=args.input_override,
            model_family=args.model_family,
            write_artifacts=args.write_artifacts,
            output_dir=args.output_dir,
            run_name=args.run_name,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
            return 0

        print("Baseline preflight completed.")
        print(f"config: {payload['config_name']}")
        print(f"phase: {payload['phase']}")
        print("can_train_now: " + ("true" if payload["can_train_now"] else "false"))
        print("training enabled: " + ("true" if payload["training_enabled"] else "false"))
        print(
            "phase policy allows training: "
            + ("true" if payload["phase_policy_allows_training"] else "false")
        )
        print("training executed: " + ("true" if payload["training_executed"] else "false"))
        print("readiness: " + ("ready" if payload["readiness_ready"] else "not_ready"))
        print("strict readiness: " + ("ready" if payload["strict_readiness_ready"] else "not_ready"))
        print("path hygiene: " + ("pass" if payload["path_hygiene_passed"] else "fail"))
        perm_map = {p["name"]: p["allowed"] for p in payload["execution_contract"]["permissions"]}
        allowed_count = sum(1 for v in perm_map.values() if v)
        forbidden_count = sum(1 for v in perm_map.values() if not v)
        print(f"permissions: allowed={allowed_count}, forbidden={forbidden_count}")
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
            print("  - baseline_preflight_report.json")
            print("  - baseline_execution_contract.json")

        non_expected = [b for b in payload["blockers"] if b not in {"Training remains disabled by Phase 10 policy."}]
        if non_expected:
            print("ERROR: non-expected blocker(s) in preflight", file=sys.stderr)
            return 1
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
