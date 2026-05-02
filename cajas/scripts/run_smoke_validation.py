#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

FIXTURE_DIR = Path("cajas/data_examples/validation_fixtures")


def _run(cmd: list[str]) -> float:
    start = time.time()
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)
    return time.time() - start


def build_tier_commands(*, py: str, out_root: Path, tier: str) -> list[list[str]]:
    micro_out = out_root / "micro"
    if tier == "micro":
        return [
            [py, "cajas/scripts/build_ci_validation_plan.py", "--out-dir", str(micro_out / "ci_plan")],
            [
                py,
                "cajas/scripts/audit_validation_runtime.py",
                "--tests-root",
                "cajas/tests",
                "--out-json",
                str(micro_out / "runtime_audit" / "validation_runtime_audit.json"),
                "--out-md",
                str(micro_out / "runtime_audit" / "validation_runtime_audit.md"),
            ],
            [
                py,
                "cajas/scripts/build_final_readiness_summary.py",
                "--packet",
                str(FIXTURE_DIR / "final_readiness_needs_manual_governance_review.json"),
                "--out",
                str(micro_out / "final_readiness" / "final_readiness_summary.md"),
            ],
            [
                py,
                "cajas/scripts/build_governance_review_decision.py",
                "--governance-remediation-report",
                str(FIXTURE_DIR / "governance_remediation_needs_manual_review.json"),
                "--final-readiness-packet",
                str(FIXTURE_DIR / "final_readiness_needs_manual_governance_review.json"),
                "--stable-reproducibility-report",
                str(FIXTURE_DIR / "stable_reproducibility_report_pass.json"),
                "--decision",
                str(FIXTURE_DIR / "governance_review_decision_approve_offline_only.json"),
                "--out-json",
                str(micro_out / "governance_review" / "governance_review_decision.json"),
                "--out-md",
                str(micro_out / "governance_review" / "governance_review_decision.md"),
            ],
            [
                py,
                "cajas/scripts/build_research_only_approval_packet.py",
                "--final-readiness-packet",
                str(FIXTURE_DIR / "final_readiness_needs_manual_governance_review.json"),
                "--stable-reproducibility-report",
                str(FIXTURE_DIR / "stable_reproducibility_report_pass.json"),
                "--governance-remediation-report",
                str(FIXTURE_DIR / "governance_remediation_needs_manual_review.json"),
                "--governance-review-decision",
                str(micro_out / "governance_review" / "governance_review_decision.json"),
                "--offline-review-packet",
                str(FIXTURE_DIR / "offline_review_packet_tiny.json"),
                "--final-research-bundle",
                str(FIXTURE_DIR / "final_research_bundle_tiny.json"),
                "--out-json",
                str(micro_out / "approval" / "research_only_approval_packet.json"),
                "--out-md",
                str(micro_out / "approval" / "research_only_approval_packet.md"),
            ],
        ]

    if tier == "minimal":
        return [
            [py, "cajas/scripts/run_research_gate_smoke.py", "--out-root", str(out_root / "research-gate-smoke")],
            [py, "cajas/scripts/run_qlib_adapter_smoke.py", "--out-root", str(out_root / "qlib-adapter-smoke")],
        ]

    if tier == "closure":
        return [
            [py, "cajas/scripts/run_governance_review_closure_smoke.py", "--out-root", str(out_root / "governance-review-smoke")],
            [py, "cajas/scripts/run_final_reproducibility_closure_smoke.py", "--out-root", str(out_root / "final-repro-closure-smoke")],
        ]

    return [
        [py, "cajas/scripts/run_full_research_stack_smoke.py", "--out-root", str(out_root / "full-research-stack-smoke")],
        [py, "cajas/scripts/run_research_quality_loop_smoke.py", "--out-root", str(out_root / "research-quality-loop-smoke")],
        [py, "cajas/scripts/run_research_remediation_smoke.py", "--out-root", str(out_root / "research-remediation-smoke")],
    ]


def main() -> int:
    p = argparse.ArgumentParser(description="Run explicit smoke validation tiers.")
    p.add_argument("--tier", choices=["micro", "minimal", "closure", "full"], default="micro")
    p.add_argument("--out-root", default="tmp/smoke-validation")
    p.add_argument("--include-real-data", action="store_true")
    p.add_argument("--data-root", default="/home/phiner/projects/research/data")
    p.add_argument("--allow-large-data", action="store_true")
    p.add_argument("--large-data-threshold-mb", type=int, default=256)
    args = p.parse_args()

    py = sys.executable
    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    if args.include_real_data:
        data_root = Path(args.data_root).expanduser().resolve()
        if data_root.exists():
            threshold = args.large_data_threshold_mb * 1024 * 1024
            large = [p for p in data_root.glob("*.csv") if p.is_file() and p.stat().st_size > threshold]
            if large and not args.allow_large_data:
                print(f"warning: {len(large)} files exceed {args.large_data_threshold_mb}MB under {data_root}")
                raise SystemExit("use --allow-large-data to acknowledge large real-data reads")
        print(f"warning: include-real-data enabled for {data_root}; micro/minimal tiers still prefer fixtures by default.")

    total = 0.0
    for cmd in build_tier_commands(py=py, out_root=out_root, tier=args.tier):
        elapsed = _run(cmd)
        total += elapsed
        print(f"elapsed: {elapsed:.2f}s")
    print(f"tier={args.tier}")
    print(f"out_root={out_root}")
    print(f"total_runtime: {total:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
