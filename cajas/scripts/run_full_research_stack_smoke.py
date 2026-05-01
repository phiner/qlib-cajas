#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run full bounded research stack hardening smoke.")
    p.add_argument("--out-root", default="tmp/full-hardening-smoke")
    args = p.parse_args()

    root = Path(args.out_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    run_a = root / "run_a"
    run_b = root / "run_b"
    _run([py, "cajas/scripts/run_final_readiness_smoke.py", "--out-root", str(run_a)])
    _run([py, "cajas/scripts/run_final_readiness_smoke.py", "--out-root", str(run_b)])

    fp_a = root / "fingerprints" / "run_a_stable_fingerprint.json"
    fp_b = root / "fingerprints" / "run_b_stable_fingerprint.json"
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_a), "--out", str(fp_a)])
    _run([py, "cajas/scripts/build_stable_fingerprint.py", "--root", str(run_b), "--out", str(fp_b)])

    stable_repro = root / "stable_repro" / "stable_reproducibility_report.json"
    _run([py, "cajas/scripts/check_stable_reproducibility.py", "--left", str(fp_a), "--right", str(fp_b), "--out", str(stable_repro)])

    final_packet = root / "final" / "final_readiness_packet.json"
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
            str(stable_repro),
            "--ci-plan",
            str(run_a / "ci" / "ci_validation_plan.json"),
            "--out",
            str(final_packet),
        ]
    )

    final_summary = root / "final" / "final_readiness_summary.md"
    _run([py, "cajas/scripts/build_final_readiness_summary.py", "--packet", str(final_packet), "--out", str(final_summary)])

    governance = root / "governance" / "research_governance_audit.json"
    _run([py, "cajas/scripts/audit_research_governance.py", "--root", "cajas", "--out", str(governance)])

    lineage_j = root / "lineage" / "artifact_lineage.json"
    lineage_m = root / "lineage" / "artifact_lineage.md"
    _run([py, "cajas/scripts/build_artifact_lineage.py", "--root", str(root), "--out-json", str(lineage_j), "--out-md", str(lineage_m)])

    catalog_j = root / "catalog" / "research_run_catalog.json"
    catalog_m = root / "catalog" / "research_run_catalog.md"
    _run([py, "cajas/scripts/build_research_run_catalog.py", "--root", str(root), "--out-json", str(catalog_j), "--out-md", str(catalog_m)])

    review_j = root / "review" / "offline_review_packet.json"
    review_m = root / "review" / "offline_review_packet.md"
    _run(
        [
            py,
            "cajas/scripts/build_offline_review_packet.py",
            "--final-readiness-packet",
            str(final_packet),
            "--stable-reproducibility-report",
            str(stable_repro),
            "--governance-audit",
            str(governance),
            "--artifact-lineage",
            str(lineage_j),
            "--run-catalog",
            str(catalog_j),
            "--out-json",
            str(review_j),
            "--out-md",
            str(review_m),
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
            str(governance),
            "--artifact-lineage",
            str(lineage_j),
            "--run-catalog",
            str(catalog_j),
            "--offline-review-packet",
            str(review_j),
            "--ci-validation-plan",
            str(run_a / "ci" / "ci_validation_plan.json"),
            "--out-json",
            str(bundle_j),
            "--out-md",
            str(bundle_m),
        ]
    )

    print("Full research stack smoke completed.")
    print(f"run_a: {run_a}")
    print(f"run_b: {run_b}")
    print(f"stable repro: {stable_repro}")
    print(f"final packet: {final_packet}")
    print(f"governance: {governance}")
    print(f"lineage json: {lineage_j}")
    print(f"catalog json: {catalog_j}")
    print(f"review json: {review_j}")
    print(f"bundle json: {bundle_j}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
