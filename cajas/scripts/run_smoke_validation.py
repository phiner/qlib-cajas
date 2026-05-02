#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run explicit smoke validation tiers.")
    p.add_argument("--tier", choices=["minimal", "full"], default="minimal")
    p.add_argument("--out-root", default="tmp/smoke-validation")
    args = p.parse_args()

    py = sys.executable
    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if args.tier == "minimal":
        _run([py, "cajas/scripts/run_governance_review_closure_smoke.py", "--out-root", str(out_root / "governance-review-smoke")])
    else:
        _run([py, "cajas/scripts/run_governance_review_closure_smoke.py", "--out-root", str(out_root / "governance-review-smoke")])
        _run([py, "cajas/scripts/run_final_reproducibility_closure_smoke.py", "--out-root", str(out_root / "final-repro-closure-smoke")])
        _run([py, "cajas/scripts/run_research_remediation_smoke.py", "--out-root", str(out_root / "research-remediation-smoke")])
    print(f"tier={args.tier}")
    print(f"out_root={out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

