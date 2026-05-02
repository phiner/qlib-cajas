#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end research quality loop smoke.")
    p.add_argument("--out-root", default="tmp/research-quality-loop-smoke")
    args = p.parse_args()

    py = sys.executable
    root = Path(args.out_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    full_stack = root / "full_stack"
    _run([py, "cajas/scripts/run_full_research_stack_smoke.py", "--out-root", str(full_stack)])

    fp_a = full_stack / "fingerprints" / "run_a_stable_fingerprint.json"
    fp_b = full_stack / "fingerprints" / "run_b_stable_fingerprint.json"
    stable_repro = full_stack / "stable_repro" / "stable_reproducibility_report.json"

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
            str(stable_repro),
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
            str(full_stack / "run_a"),
            "--out-json",
            str(norm_j),
            "--out-md",
            str(norm_m),
        ]
    )

    governance_audit = full_stack / "governance" / "research_governance_audit.json"
    gov_j = root / "governance" / "governance_remediation_report.json"
    gov_m = root / "governance" / "governance_remediation_report.md"
    _run(
        [
            py,
            "cajas/scripts/build_governance_remediation_report.py",
            "--governance-audit",
            str(governance_audit),
            "--out-json",
            str(gov_j),
            "--out-md",
            str(gov_m),
        ]
    )

    final_packet = root / "final" / "final_readiness_packet.json"
    _run(
        [
            py,
            "cajas/scripts/build_final_readiness_packet.py",
            "--gate-packet",
            str(full_stack / "run_a" / "run_a" / "gate" / "research_gate_packet.json"),
            "--no-broker-packet",
            str(full_stack / "run_a" / "run_a" / "no_broker" / "no_broker_dry_run_packet.json"),
            "--manifest",
            str(full_stack / "run_a" / "manifests" / "run_a_manifest.json"),
            "--reproducibility-report",
            str(full_stack / "run_a" / "repro" / "reproducibility_report.json"),
            "--stable-reproducibility-report",
            str(stable_repro),
            "--stable-reproducibility-explanation",
            str(explain_j),
            "--governance-remediation-report",
            str(gov_j),
            "--normalization-coverage-report",
            str(norm_j),
            "--ci-plan",
            str(full_stack / "run_a" / "ci" / "ci_validation_plan.json"),
            "--out",
            str(final_packet),
        ]
    )
    final_summary = root / "final" / "final_readiness_summary.md"
    _run([py, "cajas/scripts/build_final_readiness_summary.py", "--packet", str(final_packet), "--out", str(final_summary)])

    reviewer_out = root / "reviewer" / "reviewer_decision_packet.json"
    _run(
        [
            py,
            "cajas/scripts/build_reviewer_decision_packet.py",
            "--decision",
            "cajas/data_examples/reviewer_decision_example.json",
            "--final-readiness-packet",
            str(final_packet),
            "--governance-remediation-report",
            str(gov_j),
            "--reproducibility-explanation",
            str(explain_j),
            "--out",
            str(reviewer_out),
        ]
    )

    bundle_j = root / "bundle" / "final_research_bundle.json"
    bundle_m = root / "bundle" / "final_research_bundle.md"
    _run(
        [
            py,
            "cajas/scripts/build_final_research_bundle.py",
            "--root",
            str(root),
            "--final-readiness-packet",
            str(final_packet),
            "--final-readiness-summary",
            str(final_summary),
            "--stable-reproducibility-report",
            str(stable_repro),
            "--governance-audit",
            str(governance_audit),
            "--artifact-lineage",
            str(full_stack / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(full_stack / "catalog" / "research_run_catalog.json"),
            "--offline-review-packet",
            str(full_stack / "review" / "offline_review_packet.json"),
            "--ci-validation-plan",
            str(full_stack / "run_a" / "ci" / "ci_validation_plan.json"),
            "--out-json",
            str(bundle_j),
            "--out-md",
            str(bundle_m),
        ]
    )

    print("Research quality loop smoke completed.")
    print(f"full_stack: {full_stack}")
    print(f"repro_explain_json: {explain_j}")
    print(f"normalization_json: {norm_j}")
    print(f"governance_remediation_json: {gov_j}")
    print(f"final_packet: {final_packet}")
    print(f"final_summary: {final_summary}")
    print(f"reviewer_decision: {reviewer_out}")
    print(f"bundle_json: {bundle_j}")
    print(f"bundle_md: {bundle_m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

