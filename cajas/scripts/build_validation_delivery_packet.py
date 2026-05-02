#!/usr/bin/env python3
"""Build validation delivery packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_delivery_packet import (
    build_validation_delivery_packet,
    generate_packet_index_markdown,
)


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build validation delivery packet")
    parser.add_argument("--packet-name", required=True, help="Packet name")
    parser.add_argument("--smoke-root", help="Smoke output root directory")
    parser.add_argument("--contract-report", help="Contract report JSON path")
    parser.add_argument("--trend-snapshot", help="Trend snapshot JSON path")
    parser.add_argument("--runtime-budget-report", help="Runtime budget report JSON path")
    parser.add_argument("--reviewer-diff-report", help="Reviewer diff report JSON path")
    parser.add_argument("--experiment-manifest", help="Qlib experiment manifest JSON path")
    parser.add_argument("--data-source-audit", help="Data source audit JSON path")
    parser.add_argument("--out-dir", required=True, help="Output directory for packet")
    parser.add_argument("--allow-missing-critical", action="store_true", help="Allow missing critical artifacts")
    parser.add_argument("--copy-artifacts", action="store_true", help="Copy artifacts into packet directory")
    args = parser.parse_args(argv)

    smoke_root = Path(args.smoke_root) if args.smoke_root else None
    contract_report = Path(args.contract_report) if args.contract_report else None
    trend_snapshot = Path(args.trend_snapshot) if args.trend_snapshot else None
    runtime_budget = Path(args.runtime_budget_report) if args.runtime_budget_report else None
    reviewer_diff = Path(args.reviewer_diff_report) if args.reviewer_diff_report else None
    experiment_manifest = Path(args.experiment_manifest) if args.experiment_manifest else None
    data_source_audit = Path(args.data_source_audit) if args.data_source_audit else None

    packet = build_validation_delivery_packet(
        packet_name=args.packet_name,
        smoke_root=smoke_root,
        contract_report_path=contract_report,
        trend_snapshot_path=trend_snapshot,
        runtime_budget_report_path=runtime_budget,
        reviewer_diff_report_path=reviewer_diff,
        experiment_manifest_path=experiment_manifest,
        data_source_audit_path=data_source_audit,
        allow_missing_critical=args.allow_missing_critical,
    )

    # Write packet manifest
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_data = {
        "packet_version": packet.packet_version,
        "packet_name": packet.packet_name,
        "created_at": packet.created_at,
        "git_branch": packet.git_branch,
        "git_commit": packet.git_commit,
        "source_roots": packet.source_roots,
        "included_artifacts": packet.included_artifacts,
        "missing_artifacts": packet.missing_artifacts,
        "overall_status": packet.overall_status,
        "dataset_quality_status": packet.dataset_quality_status,
        "dataset_quality_score": packet.dataset_quality_score,
        "contract_status": packet.contract_status,
        "contract_error_count": packet.contract_error_count,
        "semantic_error_count": packet.semantic_error_count,
        "drift_breaking_count": packet.drift_breaking_count,
        "trend_quality_score": packet.trend_quality_score,
        "runtime_budget_status": packet.runtime_budget_status,
        "reviewer_diff_status": packet.reviewer_diff_status,
        "data_source_audit_read_count": packet.data_source_audit_read_count,
        "reviewer_notes": packet.reviewer_notes,
    }

    safe_json_write(out_dir / "packet_manifest.json", manifest_data)

    # Write packet index
    markdown = generate_packet_index_markdown(packet)
    (out_dir / "packet_index.md").write_text(markdown, encoding="utf-8")

    # Copy artifacts if requested
    if args.copy_artifacts:
        artifacts_dir = out_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        for artifact in packet.included_artifacts:
            src_path = Path(artifact["path"])
            if src_path.exists() and src_path.is_file():
                dest_name = f"{artifact['name']}_{src_path.name}"
                dest_path = artifacts_dir / dest_name
                dest_path.write_bytes(src_path.read_bytes())

    # Determine exit code
    if packet.overall_status == "fail":
        print(
            json.dumps({"status": "fail", "overall_status": packet.overall_status}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"status": "ok", "overall_status": packet.overall_status}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
