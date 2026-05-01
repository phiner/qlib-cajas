#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end research gate + no-broker dry-run smoke.")
    p.add_argument("--out-root", default="tmp/research-gate-smoke")
    args = p.parse_args()

    root = Path(args.out_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    model_bridge_root = root / "model_bridge"
    gate_dir = root / "gate"
    nb_dir = root / "no_broker"
    summary_dir = root / "summary"

    _run([py, "cajas/scripts/run_qlib_model_bridge_smoke.py", "--out-root", str(model_bridge_root)])

    gate_packet = gate_dir / "research_gate_packet.json"
    _run(
        [
            py,
            "cajas/scripts/build_research_gate_packet.py",
            "--contract",
            str(model_bridge_root / "contract" / "qlib_model_training_contract.json"),
            "--experiment-dir",
            str(model_bridge_root / "experiment"),
            "--registry",
            str(model_bridge_root / "registry" / "model_run_registry.jsonl"),
            "--comparison",
            str(model_bridge_root / "comparison" / "model_run_comparison.json"),
            "--handler-smoke-report",
            str(model_bridge_root / "dataset_handler" / "validation" / "qlib_handler_smoke_report.json"),
            "--out",
            str(gate_packet),
        ]
    )

    nb_packet = nb_dir / "no_broker_dry_run_packet.json"
    _run([py, "cajas/scripts/build_no_broker_dry_run_packet.py", "--gate-packet", str(gate_packet), "--out", str(nb_packet)])

    summary_path = summary_dir / "research_gate_summary.md"
    _run([py, "cajas/scripts/build_research_gate_summary.py", "--gate-packet", str(gate_packet), "--no-broker-packet", str(nb_packet), "--out", str(summary_path)])

    print("Research gate smoke completed.")
    print(f"model_bridge: {model_bridge_root}")
    print(f"gate packet: {gate_packet}")
    print(f"no_broker packet: {nb_packet}")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
