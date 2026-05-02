#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run manual governance review closure smoke.")
    p.add_argument("--out-root", default="tmp/governance-review-smoke")
    args = p.parse_args()
    py = sys.executable
    root = Path(args.out_root).expanduser().resolve()
    repro = root / "repro_closure"
    _run([py, "cajas/scripts/run_final_reproducibility_closure_smoke.py", "--out-root", str(repro)])

    gov_j = root / "governance_review" / "governance_review_decision.json"
    gov_m = root / "governance_review" / "governance_review_decision.md"
    _run(
        [
            py,
            "cajas/scripts/build_governance_review_decision.py",
            "--governance-remediation-report",
            str(repro / "governance" / "governance_remediation_report.json"),
            "--final-readiness-packet",
            str(repro / "final" / "final_readiness_packet.json"),
            "--stable-reproducibility-report",
            str(repro / "stable_repro" / "stable_reproducibility_report.json"),
            "--decision",
            "cajas/data_examples/governance_review_decision_example.json",
            "--out-json",
            str(gov_j),
            "--out-md",
            str(gov_m),
        ]
    )

    approval_j = root / "approval" / "research_only_approval_packet.json"
    approval_m = root / "approval" / "research_only_approval_packet.md"
    _run(
        [
            py,
            "cajas/scripts/build_research_only_approval_packet.py",
            "--final-readiness-packet",
            str(repro / "final" / "final_readiness_packet.json"),
            "--stable-reproducibility-report",
            str(repro / "stable_repro" / "stable_reproducibility_report.json"),
            "--governance-remediation-report",
            str(repro / "governance" / "governance_remediation_report.json"),
            "--governance-review-decision",
            str(gov_j),
            "--offline-review-packet",
            str(repro / "review" / "offline_review_packet.json"),
            "--final-research-bundle",
            str(repro / "bundle" / "final_research_bundle.json"),
            "--out-json",
            str(approval_j),
            "--out-md",
            str(approval_m),
        ]
    )

    final_j = root / "final" / "final_readiness_packet.json"
    final_m = root / "final" / "final_readiness_summary.md"
    _run(
        [
            py,
            "cajas/scripts/build_final_readiness_packet.py",
            "--gate-packet",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "run_a" / "gate" / "research_gate_packet.json"),
            "--no-broker-packet",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "run_a" / "no_broker" / "no_broker_dry_run_packet.json"),
            "--manifest",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "manifests" / "run_a_manifest.json"),
            "--reproducibility-report",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "repro" / "reproducibility_report.json"),
            "--stable-reproducibility-report",
            str(repro / "stable_repro" / "stable_reproducibility_report.json"),
            "--stable-reproducibility-explanation",
            str(repro / "repro_explain" / "stable_reproducibility_explanation.json"),
            "--governance-remediation-report",
            str(repro / "governance" / "governance_remediation_report.json"),
            "--normalization-coverage-report",
            str(repro / "normalization" / "normalization_coverage_report.json"),
            "--governance-review-decision",
            str(gov_j),
            "--research-only-approval-packet",
            str(approval_j),
            "--ci-plan",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "ci" / "ci_validation_plan.json"),
            "--out",
            str(final_j),
        ]
    )
    _run([py, "cajas/scripts/build_final_readiness_summary.py", "--packet", str(final_j), "--out", str(final_m)])

    review_j = root / "review" / "offline_review_packet.json"
    review_m = root / "review" / "offline_review_packet.md"
    _run(
        [
            py,
            "cajas/scripts/build_offline_review_packet.py",
            "--final-readiness-packet",
            str(final_j),
            "--stable-reproducibility-report",
            str(repro / "stable_repro" / "stable_reproducibility_report.json"),
            "--governance-audit",
            str(repro / "remediation" / "governance" / "research_governance_audit.json"),
            "--artifact-lineage",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "catalog" / "research_run_catalog.json"),
            "--governance-review-decision",
            str(gov_j),
            "--research-only-approval-packet",
            str(approval_j),
            "--out-json",
            str(review_j),
            "--out-md",
            str(review_m),
        ]
    )

    _run(
        [
            py,
            "cajas/scripts/build_final_research_bundle.py",
            "--root",
            str(root),
            "--final-readiness-packet",
            str(final_j),
            "--final-readiness-summary",
            str(final_m),
            "--stable-reproducibility-report",
            str(repro / "stable_repro" / "stable_reproducibility_report.json"),
            "--governance-audit",
            str(repro / "remediation" / "governance" / "research_governance_audit.json"),
            "--artifact-lineage",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "catalog" / "research_run_catalog.json"),
            "--offline-review-packet",
            str(review_j),
            "--ci-validation-plan",
            str(repro / "remediation" / "quality_loop" / "full_stack" / "run_a" / "ci" / "ci_validation_plan.json"),
            "--governance-review-decision",
            str(gov_j),
            "--research-only-approval-packet",
            str(approval_j),
            "--out-json",
            str(root / "bundle" / "final_research_bundle.json"),
            "--out-md",
            str(root / "bundle" / "final_research_bundle.md"),
        ]
    )
    print(f"governance_review_decision: {gov_j}")
    print(f"approval_packet: {approval_j}")
    print(f"final_packet: {final_j}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

