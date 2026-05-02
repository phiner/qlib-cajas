#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Run final stable reproducibility closure smoke.")
    p.add_argument("--out-root", default="tmp/final-repro-closure-smoke")
    args = p.parse_args()
    py = sys.executable
    root = Path(args.out_root).expanduser().resolve()
    remediation = root / "remediation"
    _run([py, "cajas/scripts/run_research_remediation_smoke.py", "--out-root", str(remediation)])

    run_a = remediation / "quality_loop" / "full_stack" / "run_a"
    run_b = remediation / "quality_loop" / "full_stack" / "run_b"
    fp_a = root / "fingerprints" / "run_a_stable_fingerprint.json"
    fp_b = root / "fingerprints" / "run_b_stable_fingerprint.json"
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_a), "--out", str(fp_a)])
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_b), "--out", str(fp_b)])

    stable = root / "stable_repro" / "stable_reproducibility_report.json"
    _run([py, "cajas/scripts/check_stable_reproducibility.py", "--left", str(fp_a), "--right", str(fp_b), "--out", str(stable)])

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
            str(stable),
            "--out-json",
            str(explain_j),
            "--out-md",
            str(explain_m),
        ]
    )

    norm_j = root / "normalization" / "normalization_coverage_report.json"
    norm_m = root / "normalization" / "normalization_coverage_report.md"
    _run([py, "cajas/scripts/build_normalization_coverage_report.py", "--stable-fingerprint", str(fp_a), "--artifacts-root", str(run_a), "--out-json", str(norm_j), "--out-md", str(norm_m)])

    gov_j = root / "governance" / "governance_remediation_report.json"
    _run(
        [
            py,
            "cajas/scripts/build_governance_remediation_report.py",
            "--governance-audit",
            str(remediation / "governance" / "research_governance_audit.json"),
            "--out-json",
            str(gov_j),
            "--out-md",
            str(root / "governance" / "governance_remediation_report.md"),
        ]
    )

    final_j = root / "final" / "final_readiness_packet.json"
    final_m = root / "final" / "final_readiness_summary.md"
    _run(
        [
            py,
            "cajas/scripts/build_final_readiness_packet.py",
            "--gate-packet",
            str(run_a / "run_a" / "gate" / "research_gate_packet.json"),
            "--no-broker-packet",
            str(run_a / "run_a" / "no_broker" / "no_broker_dry_run_packet.json"),
            "--manifest",
            str(run_a / "manifests" / "run_a_manifest.json"),
            "--reproducibility-report",
            str(run_a / "repro" / "reproducibility_report.json"),
            "--stable-reproducibility-report",
            str(stable),
            "--stable-reproducibility-explanation",
            str(explain_j),
            "--governance-remediation-report",
            str(gov_j),
            "--normalization-coverage-report",
            str(norm_j),
            "--ci-plan",
            str(run_a / "ci" / "ci_validation_plan.json"),
            "--out",
            str(final_j),
        ]
    )
    _run([py, "cajas/scripts/build_final_readiness_summary.py", "--packet", str(final_j), "--out", str(final_m)])

    _run(
        [
            py,
            "cajas/scripts/build_offline_review_packet.py",
            "--final-readiness-packet",
            str(final_j),
            "--stable-reproducibility-report",
            str(stable),
            "--governance-audit",
            str(remediation / "governance" / "research_governance_audit.json"),
            "--artifact-lineage",
            str(remediation / "quality_loop" / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(remediation / "quality_loop" / "full_stack" / "catalog" / "research_run_catalog.json"),
            "--out-json",
            str(root / "review" / "offline_review_packet.json"),
            "--out-md",
            str(root / "review" / "offline_review_packet.md"),
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
            str(stable),
            "--governance-audit",
            str(remediation / "governance" / "research_governance_audit.json"),
            "--artifact-lineage",
            str(remediation / "quality_loop" / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(remediation / "quality_loop" / "full_stack" / "catalog" / "research_run_catalog.json"),
            "--offline-review-packet",
            str(root / "review" / "offline_review_packet.json"),
            "--ci-validation-plan",
            str(run_a / "ci" / "ci_validation_plan.json"),
            "--out-json",
            str(root / "bundle" / "final_research_bundle.json"),
            "--out-md",
            str(root / "bundle" / "final_research_bundle.md"),
        ]
    )

    before = _load(remediation / "final" / "final_readiness_packet.json")
    after = _load(final_j)
    print(
        "before final_readiness={} stable={} governance={}".format(
            before.get("final_status"),
            _load(remediation / "quality_loop" / "full_stack" / "stable_repro" / "stable_reproducibility_report.json").get("final_status"),
            _load(remediation / "governance" / "governance_remediation_report.json").get("final_suggested_status"),
        )
    )
    print(
        "after  final_readiness={} stable={} governance={}".format(
            after.get("final_status"),
            _load(stable).get("final_status"),
            _load(gov_j).get("final_suggested_status"),
        )
    )
    print(f"final packet: {final_j}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

