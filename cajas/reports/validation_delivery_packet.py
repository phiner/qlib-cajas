"""Validation delivery packet generation."""

from __future__ import annotations

import datetime
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationDeliveryPacket:
    """Validation delivery packet."""

    packet_version: str
    packet_name: str
    created_at: str
    git_branch: str | None
    git_commit: str | None
    source_roots: list[str]
    included_artifacts: list[dict]
    missing_artifacts: list[dict]
    overall_status: str
    dataset_quality_status: str | None
    dataset_quality_score: float | None
    contract_status: str | None
    contract_error_count: int | None
    semantic_error_count: int | None
    drift_breaking_count: int | None
    trend_quality_score: float | None
    runtime_budget_status: str | None
    reviewer_diff_status: str | None
    data_source_audit_read_count: int | None
    reviewer_notes: list[str]


def get_git_info() -> tuple[str | None, str | None]:
    """Get git branch and commit."""
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL, text=True).strip()
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        return branch or None, commit or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None


def safe_read_json(path: Path) -> dict | None:
    """Safely read JSON file."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def build_validation_delivery_packet(
    packet_name: str,
    smoke_root: Path | None = None,
    contract_report_path: Path | None = None,
    trend_snapshot_path: Path | None = None,
    runtime_budget_report_path: Path | None = None,
    reviewer_diff_report_path: Path | None = None,
    experiment_manifest_path: Path | None = None,
    data_source_audit_path: Path | None = None,
    allow_missing_critical: bool = False,
    created_at: str | None = None,
    git_branch: str | None = None,
    git_commit: str | None = None,
) -> ValidationDeliveryPacket:
    """Build validation delivery packet."""
    if created_at is None:
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if git_branch is None or git_commit is None:
        git_branch, git_commit = get_git_info()

    source_roots = []
    if smoke_root:
        source_roots.append(str(smoke_root))

    included_artifacts = []
    missing_artifacts = []
    reviewer_notes = []

    # Critical artifacts
    critical_artifacts = [
        ("dataset_quality_report", smoke_root / "dataset_quality" / "dataset_quality_report.json" if smoke_root else None, "Dataset quality report"),
        ("contract_report", contract_report_path, "Contract validation report"),
    ]

    # Optional artifacts
    optional_artifacts = [
        ("trend_snapshot", trend_snapshot_path, "Trend snapshot"),
        ("runtime_budget_report", runtime_budget_report_path, "Runtime budget report"),
        ("reviewer_diff_report", reviewer_diff_report_path, "Reviewer diff report"),
        ("experiment_manifest", experiment_manifest_path, "Qlib experiment manifest"),
        ("data_source_audit", data_source_audit_path, "Data source audit"),
    ]

    # Check critical artifacts
    for name, path, description in critical_artifacts:
        if path and path.exists():
            included_artifacts.append({"name": name, "path": str(path), "description": description, "critical": True})
        else:
            missing_artifacts.append({"name": name, "path": str(path) if path else "not specified", "description": description, "critical": True})

    # Check optional artifacts
    for name, path, description in optional_artifacts:
        if path and path.exists():
            included_artifacts.append({"name": name, "path": str(path), "description": description, "critical": False})
        else:
            missing_artifacts.append({"name": name, "path": str(path) if path else "not specified", "description": description, "critical": False})

    # Extract status from artifacts
    dataset_quality_status = None
    dataset_quality_score = None
    contract_status = None
    contract_error_count = None
    semantic_error_count = None
    drift_breaking_count = None
    trend_quality_score = None
    runtime_budget_status = None
    reviewer_diff_status = None
    data_source_audit_read_count = None

    # Read dataset quality report
    dq_path = smoke_root / "dataset_quality" / "dataset_quality_report.json" if smoke_root else None
    if dq_path:
        dq_report = safe_read_json(dq_path)
        if dq_report:
            dataset_quality_status = dq_report.get("status")
            dataset_quality_score = dq_report.get("quality_score", {}).get("score")

    # Read contract report
    if contract_report_path:
        contract_report = safe_read_json(contract_report_path)
        if contract_report:
            contract_status = contract_report.get("status")
            contract_error_count = contract_report.get("error_count")
            semantic_error_count = contract_report.get("semantic_error_count")
            drift_breaking_count = contract_report.get("drift_summary", {}).get("breaking_count")

    # Read trend snapshot
    if trend_snapshot_path:
        trend_snapshot = safe_read_json(trend_snapshot_path)
        if trend_snapshot:
            trend_quality_score = trend_snapshot.get("quality_score")

    # Read runtime budget report
    if runtime_budget_report_path:
        budget_report = safe_read_json(runtime_budget_report_path)
        if budget_report:
            runtime_budget_status = budget_report.get("overall_status")
            # Extract measured fast_total if available
            if "results" in budget_report:
                for result in budget_report["results"]:
                    if result.get("component") == "fast_total" and result.get("observed_seconds") is not None:
                        # Store in a new field for delivery packet
                        pass  # Will be added to packet dataclass if needed

    # Read reviewer diff report
    if reviewer_diff_report_path:
        diff_report = safe_read_json(reviewer_diff_report_path)
        if diff_report:
            reviewer_diff_status = diff_report.get("overall_status")

    # Read data source audit
    if data_source_audit_path:
        audit_report = safe_read_json(data_source_audit_path)
        if audit_report:
            data_source_audit_read_count = audit_report.get("read_csv_count")

    # Determine overall status
    overall_status = "pass"

    # Check critical missing artifacts
    critical_missing = [a for a in missing_artifacts if a["critical"]]
    if critical_missing and not allow_missing_critical:
        overall_status = "fail"
        reviewer_notes.append(f"Critical artifacts missing: {', '.join(a['name'] for a in critical_missing)}")

    # Check contract status
    if contract_status == "fail":
        overall_status = "fail"
        reviewer_notes.append("Contract validation failed")

    # Check semantic errors
    if semantic_error_count and semantic_error_count > 0:
        overall_status = "fail"
        reviewer_notes.append(f"Semantic errors detected: {semantic_error_count}")

    # Warn conditions
    if overall_status == "pass":
        optional_missing = [a for a in missing_artifacts if not a["critical"]]
        if optional_missing:
            overall_status = "warn"
            reviewer_notes.append(f"Optional artifacts missing: {', '.join(a['name'] for a in optional_missing)}")

        if runtime_budget_status in ("warn", "fail"):
            if overall_status == "pass":
                overall_status = "warn"
            reviewer_notes.append(f"Runtime budget status: {runtime_budget_status}")

        if reviewer_diff_status == "fail":
            overall_status = "warn"
            reviewer_notes.append("Reviewer diff detected failures")

    if not reviewer_notes:
        reviewer_notes.append("All critical artifacts present and passing")

    return ValidationDeliveryPacket(
        packet_version="v1",
        packet_name=packet_name,
        created_at=created_at,
        git_branch=git_branch,
        git_commit=git_commit,
        source_roots=source_roots,
        included_artifacts=included_artifacts,
        missing_artifacts=missing_artifacts,
        overall_status=overall_status,
        dataset_quality_status=dataset_quality_status,
        dataset_quality_score=dataset_quality_score,
        contract_status=contract_status,
        contract_error_count=contract_error_count,
        semantic_error_count=semantic_error_count,
        drift_breaking_count=drift_breaking_count,
        trend_quality_score=trend_quality_score,
        runtime_budget_status=runtime_budget_status,
        reviewer_diff_status=reviewer_diff_status,
        data_source_audit_read_count=data_source_audit_read_count,
        reviewer_notes=reviewer_notes,
    )


def generate_packet_index_markdown(packet: ValidationDeliveryPacket) -> str:
    """Generate packet index Markdown."""
    lines = [
        f"# Validation Delivery Packet: {packet.packet_name}",
        "",
        "**Important**: This packet summarizes offline Qlib research infrastructure validation artifacts only. It is not a trading, execution, alpha, or model performance report.",
        "",
        "## Executive Summary",
        "",
        f"- overall_status: `{packet.overall_status}`",
        f"- packet_version: `{packet.packet_version}`",
        f"- created_at: `{packet.created_at}`",
        f"- git_branch: `{packet.git_branch or 'unknown'}`",
        f"- git_commit: `{packet.git_commit or 'unknown'}`",
        "",
        "## Summary",
        "",
        f"- dataset_quality_status: `{packet.dataset_quality_status or 'N/A'}`",
        f"- dataset_quality_score: `{packet.dataset_quality_score or 'N/A'}`",
        f"- contract_status: `{packet.contract_status or 'N/A'}`",
        f"- contract_error_count: `{packet.contract_error_count or 0}`",
        f"- semantic_error_count: `{packet.semantic_error_count or 0}`",
        f"- drift_breaking_count: `{packet.drift_breaking_count or 0}`",
        f"- trend_quality_score: `{packet.trend_quality_score or 'N/A'}`",
        f"- runtime_budget_status: `{packet.runtime_budget_status or 'N/A'}`",
        f"- reviewer_diff_status: `{packet.reviewer_diff_status or 'N/A'}`",
        f"- data_source_audit_read_count: `{packet.data_source_audit_read_count or 'N/A'}`",
        "",
        "## Artifact Index",
        "",
        "| Artifact | Path | Status | Role |",
        "|----------|------|--------|------|",
    ]

    for artifact in packet.included_artifacts:
        critical_marker = "🔴 critical" if artifact["critical"] else "optional"
        lines.append(f"| {artifact['name']} | `{artifact['path']}` | ✅ present | {critical_marker} |")

    for artifact in packet.missing_artifacts:
        critical_marker = "🔴 critical" if artifact["critical"] else "optional"
        lines.append(f"| {artifact['name']} | `{artifact['path']}` | ❌ missing | {critical_marker} |")

    lines.extend([
        "",
        "## Reviewer Notes",
        "",
    ])

    for note in packet.reviewer_notes:
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Recommended Action",
        "",
    ])

    if packet.overall_status == "pass":
        lines.append("**Ready for reviewer**: All critical artifacts present and passing.")
    elif packet.overall_status == "warn":
        lines.append("**Review warnings before merge**: Some optional artifacts missing or warnings detected.")
    else:
        lines.append("**Fix failing validation before merge**: Critical artifacts missing or validation failures detected.")

    lines.append("")
    return "\n".join(lines)
