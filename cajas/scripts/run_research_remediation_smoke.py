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
    p = argparse.ArgumentParser(description="Run remediation smoke for semantic repro + governance blockers.")
    p.add_argument("--out-root", default="tmp/research-remediation-smoke")
    args = p.parse_args()
    py = sys.executable
    root = Path(args.out_root).expanduser().resolve()
    qroot = root / "quality_loop"
    _run([py, "cajas/scripts/run_research_quality_loop_smoke.py", "--out-root", str(qroot)])

    before_final = _load(qroot / "final" / "final_readiness_packet.json").get("final_status")
    before_stable = _load(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json").get("final_status")
    before_gov = _load(qroot / "governance" / "governance_remediation_report.json").get("final_suggested_status")

    blockers_j = root / "blockers" / "research_blocker_localization.json"
    blockers_m = root / "blockers" / "research_blocker_localization.md"
    _run(
        [
            py,
            "cajas/scripts/localize_research_blockers.py",
            "--stable-repro-report",
            str(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json"),
            "--repro-explanation",
            str(qroot / "repro_explain" / "stable_reproducibility_explanation.json"),
            "--normalization-coverage",
            str(qroot / "normalization" / "normalization_coverage_report.json"),
            "--governance-audit",
            str(qroot / "full_stack" / "governance" / "research_governance_audit.json"),
            "--governance-remediation",
            str(qroot / "governance" / "governance_remediation_report.json"),
            "--final-readiness",
            str(qroot / "final" / "final_readiness_packet.json"),
            "--out-json",
            str(blockers_j),
            "--out-md",
            str(blockers_m),
        ]
    )

    stable_repro = root / "stable_repro" / "stable_reproducibility_report.json"
    stable_repro.parent.mkdir(parents=True, exist_ok=True)
    stable_repro.write_text((qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json").read_text(encoding="utf-8"), encoding="utf-8")

    gov_audit = root / "governance" / "research_governance_audit.json"
    gov_rem_j = root / "governance" / "governance_remediation_report.json"
    gov_rem_m = root / "governance" / "governance_remediation_report.md"
    _run([py, "cajas/scripts/audit_research_governance.py", "--root", "cajas", "--out", str(gov_audit)])
    _run([py, "cajas/scripts/build_governance_remediation_report.py", "--governance-audit", str(gov_audit), "--out-json", str(gov_rem_j), "--out-md", str(gov_rem_m)])

    final_j = root / "final" / "final_readiness_packet.json"
    final_m = root / "final" / "final_readiness_summary.md"
    _run(
        [
            py,
            "cajas/scripts/build_final_readiness_packet.py",
            "--gate-packet",
            str(qroot / "full_stack" / "run_a" / "run_a" / "gate" / "research_gate_packet.json"),
            "--no-broker-packet",
            str(qroot / "full_stack" / "run_a" / "run_a" / "no_broker" / "no_broker_dry_run_packet.json"),
            "--manifest",
            str(qroot / "full_stack" / "run_a" / "manifests" / "run_a_manifest.json"),
            "--reproducibility-report",
            str(qroot / "full_stack" / "run_a" / "repro" / "reproducibility_report.json"),
            "--stable-reproducibility-report",
            str(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json"),
            "--stable-reproducibility-explanation",
            str(qroot / "repro_explain" / "stable_reproducibility_explanation.json"),
            "--governance-remediation-report",
            str(gov_rem_j),
            "--normalization-coverage-report",
            str(qroot / "normalization" / "normalization_coverage_report.json"),
            "--ci-plan",
            str(qroot / "full_stack" / "run_a" / "ci" / "ci_validation_plan.json"),
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
            str(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json"),
            "--governance-audit",
            str(gov_audit),
            "--artifact-lineage",
            str(qroot / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(qroot / "full_stack" / "catalog" / "research_run_catalog.json"),
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
            str(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json"),
            "--governance-audit",
            str(gov_audit),
            "--artifact-lineage",
            str(qroot / "full_stack" / "lineage" / "artifact_lineage.json"),
            "--run-catalog",
            str(qroot / "full_stack" / "catalog" / "research_run_catalog.json"),
            "--offline-review-packet",
            str(root / "review" / "offline_review_packet.json"),
            "--ci-validation-plan",
            str(qroot / "full_stack" / "run_a" / "ci" / "ci_validation_plan.json"),
            "--out-json",
            str(root / "bundle" / "final_research_bundle.json"),
            "--out-md",
            str(root / "bundle" / "final_research_bundle.md"),
        ]
    )

    after_final = _load(final_j).get("final_status")
    after_stable = _load(qroot / "full_stack" / "stable_repro" / "stable_reproducibility_report.json").get("final_status")
    after_gov = _load(gov_rem_j).get("final_suggested_status")
    print(f"before final_readiness={before_final} stable={before_stable} governance={before_gov}")
    print(f"after  final_readiness={after_final} stable={after_stable} governance={after_gov}")
    print(f"blockers: {blockers_j}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

