#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end final readiness smoke.")
    p.add_argument("--out-root", default="tmp/final-readiness-smoke")
    args = p.parse_args()

    root = Path(args.out_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    run_a = root / "run_a"
    run_b = root / "run_b"
    _run([py, "cajas/scripts/run_research_gate_smoke.py", "--out-root", str(run_a)])
    _run([py, "cajas/scripts/run_research_gate_smoke.py", "--out-root", str(run_b)])

    manifests = root / "manifests"
    man_a = manifests / "run_a_manifest.json"
    man_b = manifests / "run_b_manifest.json"
    _run([py, "cajas/scripts/build_research_pipeline_manifest.py", "--root", str(run_a), "--out", str(man_a)])
    _run([py, "cajas/scripts/build_research_pipeline_manifest.py", "--root", str(run_b), "--out", str(man_b)])

    repro = root / "repro" / "reproducibility_report.json"
    _run([py, "cajas/scripts/check_reproducibility.py", "--left", str(man_a), "--right", str(man_b), "--out", str(repro)])

    ci_dir = root / "ci"
    _run([py, "cajas/scripts/build_ci_validation_plan.py", "--out-dir", str(ci_dir)])

    final_packet = root / "final" / "final_readiness_packet.json"
    _run(
        [
            py,
            "cajas/scripts/build_final_readiness_packet.py",
            "--gate-packet",
            str(run_a / "gate" / "research_gate_packet.json"),
            "--no-broker-packet",
            str(run_a / "no_broker" / "no_broker_dry_run_packet.json"),
            "--manifest",
            str(man_a),
            "--reproducibility-report",
            str(repro),
            "--ci-plan",
            str(ci_dir / "ci_validation_plan.json"),
            "--out",
            str(final_packet),
        ]
    )

    summary = root / "final" / "final_readiness_summary.md"
    _run([py, "cajas/scripts/build_final_readiness_summary.py", "--packet", str(final_packet), "--out", str(summary)])

    print("Final readiness smoke completed.")
    print(f"run_a: {run_a}")
    print(f"run_b: {run_b}")
    print(f"manifest_a: {man_a}")
    print(f"manifest_b: {man_b}")
    print(f"repro: {repro}")
    print(f"ci plan: {ci_dir / 'ci_validation_plan.json'}")
    print(f"final packet: {final_packet}")
    print(f"final summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
