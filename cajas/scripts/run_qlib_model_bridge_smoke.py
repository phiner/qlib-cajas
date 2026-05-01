#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end qlib model bridge smoke.")
    p.add_argument("--out-root", default="tmp/qlib-model-bridge-smoke")
    args = p.parse_args()

    out = Path(args.out_root).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    _run([py, "cajas/scripts/run_qlib_dataset_handler_smoke.py", "--out-root", str(out / "dataset_handler")])

    contract = out / "contract" / "qlib_model_training_contract.json"
    _run(
        [
            py,
            "cajas/scripts/build_qlib_model_training_contract.py",
            "--handler-input",
            str(out / "dataset_handler" / "handler_input" / "handler_input.csv"),
            "--handler-manifest",
            str(out / "dataset_handler" / "handler_input" / "handler_input_manifest.json"),
            "--dataset-contract",
            str(out / "dataset_handler" / "dataset_contract" / "qlib_dataset_contract.json"),
            "--handler-smoke-report",
            str(out / "dataset_handler" / "validation" / "qlib_handler_smoke_report.json"),
            "--out",
            str(contract),
        ]
    )

    exp = out / "experiment"
    _run([py, "cajas/scripts/train_qlib_model_bridge_baseline.py", "--training-contract", str(contract), "--out-dir", str(exp), "--seed", "42", "--max-rows", "2000"])

    registry = out / "registry" / "model_run_registry.jsonl"
    _run([py, "cajas/scripts/register_qlib_model_run.py", "--experiment-dir", str(exp), "--registry", str(registry)])

    comparison = out / "comparison" / "model_run_comparison.json"
    _run([py, "cajas/scripts/compare_qlib_model_runs.py", "--registry", str(registry), "--out", str(comparison)])

    print("Qlib model bridge smoke completed.")
    print(f"contract: {contract}")
    print(f"experiment: {exp}")
    print(f"registry: {registry}")
    print(f"comparison: {comparison}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
