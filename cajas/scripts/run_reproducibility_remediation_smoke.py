#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run reproducibility remediation smoke.")
    p.add_argument("--out-root", default="tmp/research-quality-loop-smoke")
    args = p.parse_args()

    py = sys.executable
    root = Path(args.out_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    run_a = root / "run_a"
    run_b = root / "run_b"
    _run([py, "cajas/scripts/run_final_readiness_smoke.py", "--out-root", str(run_a)])
    _run([py, "cajas/scripts/run_final_readiness_smoke.py", "--out-root", str(run_b)])

    fp_a = root / "fingerprints" / "run_a_stable_fingerprint.json"
    fp_b = root / "fingerprints" / "run_b_stable_fingerprint.json"
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_a), "--out", str(fp_a)])
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_b), "--out", str(fp_b)])

    repro = root / "stable_repro" / "stable_reproducibility_report.json"
    _run([py, "cajas/scripts/check_stable_reproducibility.py", "--left", str(fp_a), "--right", str(fp_b), "--out", str(repro)])

    explain_j = root / "repro_explain" / "stable_reproducibility_explanation.json"
    explain_m = root / "repro_explain" / "stable_reproducibility_explanation.md"
    _run(
        [
            py,
            "cajas/scripts/explain_stable_reproducibility.py",
            "--left-fingerprint",
            str(fp_a),
            "--right-fingerprint",
            str(fp_b),
            "--stable-repro-report",
            str(repro),
            "--out-json",
            str(explain_j),
            "--out-md",
            str(explain_m),
        ]
    )

    norm_j = root / "normalization" / "normalization_coverage_report.json"
    norm_m = root / "normalization" / "normalization_coverage_report.md"
    _run(
        [
            py,
            "cajas/scripts/build_normalization_coverage_report.py",
            "--stable-fingerprint",
            str(fp_a),
            "--artifacts-root",
            str(run_a),
            "--out-json",
            str(norm_j),
            "--out-md",
            str(norm_m),
        ]
    )
    print(f"stable_repro_report: {repro}")
    print(f"repro_explanation_json: {explain_j}")
    print(f"normalization_coverage_json: {norm_j}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

