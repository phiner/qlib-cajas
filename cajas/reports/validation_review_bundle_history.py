"""Validation review bundle history tracking."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class BundleHistorySnapshot:
    """Snapshot of validation review bundle state."""
    snapshot_version: str
    created_at: str
    branch: str
    commit: str
    bundle_name: str
    bundle_status: str | None
    delivery_packet_status: str | None
    runtime_budget_status: str | None
    reviewer_diff_status: str | None
    fast_total_seconds: float | None
    pytest_fast_seconds: float | None
    dataset_quality_status: str | None
    dataset_quality_score: float | None
    contract_status: str | None
    contract_error_count: int | None
    semantic_error_count: int | None
    drift_breaking_count: int | None
    data_source_read_csv_count: int | None
    present_artifact_count: int | None
    missing_required_count: int | None
    missing_optional_count: int | None
    reviewer_notes: list[str]


def create_snapshot_from_bundle(
    bundle_root: Path,
    branch: str | None = None,
    commit: str | None = None,
    created_at: str | None = None,
) -> BundleHistorySnapshot:
    """Create snapshot from bundle artifacts."""
    # Read bundle manifest
    manifest_path = bundle_root / "review_bundle_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

    # Read delivery packet manifest
    packet_manifest_path = bundle_root / "delivery_packet" / "packet_manifest.json"
    packet_manifest = {}
    if packet_manifest_path.exists():
        with open(packet_manifest_path, encoding="utf-8") as f:
            packet_manifest = json.load(f)

    # Read runtime budget report
    budget_report_path = bundle_root / "validation_runtime_budget_report.json"
    budget_report = {}
    if budget_report_path.exists():
        with open(budget_report_path, encoding="utf-8") as f:
            budget_report = json.load(f)

    # Extract data
    bundle_name = manifest.get("bundle_name", "unknown")
    branch = branch or manifest.get("git_branch", "unknown")
    commit = commit or manifest.get("git_commit", "unknown")
    created_at = created_at or datetime.now(timezone.utc).isoformat()

    # Extract statuses
    delivery_packet_status = manifest.get("delivery_packet_status") or packet_manifest.get("overall_status")
    runtime_budget_status = manifest.get("runtime_budget_status") or budget_report.get("overall_status")
    reviewer_diff_status = manifest.get("reviewer_diff_status")

    # Extract runtime data
    fast_total_seconds = None
    pytest_fast_seconds = None
    if budget_report.get("results"):
        for result in budget_report["results"]:
            if result.get("component") == "fast_total":
                fast_total_seconds = result.get("observed_seconds")
            elif result.get("component") == "pytest_fast":
                pytest_fast_seconds = result.get("observed_seconds")

    # Extract dataset quality data
    dataset_quality_status = packet_manifest.get("dataset_quality_status")
    dataset_quality_score = packet_manifest.get("dataset_quality_score")
    contract_status = packet_manifest.get("contract_status")
    contract_error_count = packet_manifest.get("contract_error_count")
    semantic_error_count = packet_manifest.get("semantic_error_count")
    drift_breaking_count = packet_manifest.get("drift_breaking_count")
    data_source_read_csv_count = packet_manifest.get("data_source_audit_read_count")

    # Count artifacts
    present_artifact_count = 0
    missing_required_count = 0
    missing_optional_count = 0
    if packet_manifest.get("artifact_index"):
        for artifact in packet_manifest["artifact_index"]:
            if artifact.get("status") == "present":
                present_artifact_count += 1
            elif artifact.get("role") == "critical":
                missing_required_count += 1
            else:
                missing_optional_count += 1

    # Reviewer notes
    reviewer_notes = []
    if not delivery_packet_status:
        reviewer_notes.append("delivery_packet_status missing")
    if not runtime_budget_status:
        reviewer_notes.append("runtime_budget_status missing")

    return BundleHistorySnapshot(
        snapshot_version="v1",
        created_at=created_at,
        branch=branch,
        commit=commit,
        bundle_name=bundle_name,
        bundle_status=None,  # Not currently tracked in manifest
        delivery_packet_status=delivery_packet_status,
        runtime_budget_status=runtime_budget_status,
        reviewer_diff_status=reviewer_diff_status,
        fast_total_seconds=fast_total_seconds,
        pytest_fast_seconds=pytest_fast_seconds,
        dataset_quality_status=dataset_quality_status,
        dataset_quality_score=dataset_quality_score,
        contract_status=contract_status,
        contract_error_count=contract_error_count,
        semantic_error_count=semantic_error_count,
        drift_breaking_count=drift_breaking_count,
        data_source_read_csv_count=data_source_read_csv_count,
        present_artifact_count=present_artifact_count,
        missing_required_count=missing_required_count,
        missing_optional_count=missing_optional_count,
        reviewer_notes=reviewer_notes,
    )


def append_snapshot(history_jsonl: Path, snapshot: BundleHistorySnapshot) -> None:
    """Append snapshot to JSONL history file."""
    history_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(history_jsonl, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(snapshot)) + "\n")


def read_snapshots(history_jsonl: Path) -> list[BundleHistorySnapshot]:
    """Read all snapshots from JSONL history file."""
    if not history_jsonl.exists():
        return []

    snapshots = []
    with open(history_jsonl, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                snapshots.append(BundleHistorySnapshot(**data))
    return snapshots


def compute_delta(current: BundleHistorySnapshot, previous: BundleHistorySnapshot) -> dict[str, Any]:
    """Compute delta between two snapshots."""
    delta = {}

    # Runtime deltas
    if current.fast_total_seconds is not None and previous.fast_total_seconds is not None:
        delta["fast_total_delta"] = current.fast_total_seconds - previous.fast_total_seconds
    if current.pytest_fast_seconds is not None and previous.pytest_fast_seconds is not None:
        delta["pytest_fast_delta"] = current.pytest_fast_seconds - previous.pytest_fast_seconds

    # Status changes
    if current.delivery_packet_status != previous.delivery_packet_status:
        delta["delivery_packet_status_change"] = f"{previous.delivery_packet_status} → {current.delivery_packet_status}"
    if current.runtime_budget_status != previous.runtime_budget_status:
        delta["runtime_budget_status_change"] = f"{previous.runtime_budget_status} → {current.runtime_budget_status}"

    # Count deltas
    if current.data_source_read_csv_count is not None and previous.data_source_read_csv_count is not None:
        delta["read_csv_count_delta"] = current.data_source_read_csv_count - previous.data_source_read_csv_count
    if current.contract_error_count is not None and previous.contract_error_count is not None:
        delta["contract_error_delta"] = current.contract_error_count - previous.contract_error_count
    if current.missing_required_count is not None and previous.missing_required_count is not None:
        delta["missing_required_delta"] = current.missing_required_count - previous.missing_required_count

    return delta


def detect_regressions(current: BundleHistorySnapshot, previous: BundleHistorySnapshot) -> list[str]:
    """Detect regressions between snapshots."""
    regressions = []

    # Status regressions
    if previous.delivery_packet_status == "pass" and current.delivery_packet_status in ("warn", "fail"):
        regressions.append(f"delivery_packet_status: pass → {current.delivery_packet_status}")
    if previous.runtime_budget_status == "pass" and current.runtime_budget_status in ("warn", "fail"):
        regressions.append(f"runtime_budget_status: pass → {current.runtime_budget_status}")

    # Runtime regressions (>10% increase)
    if current.fast_total_seconds and previous.fast_total_seconds:
        if current.fast_total_seconds > previous.fast_total_seconds * 1.1:
            delta = current.fast_total_seconds - previous.fast_total_seconds
            regressions.append(f"fast_total increased by {delta:.2f}s ({delta/previous.fast_total_seconds*100:.1f}%)")

    # Data source regressions
    if current.data_source_read_csv_count and previous.data_source_read_csv_count:
        if current.data_source_read_csv_count > previous.data_source_read_csv_count:
            delta = current.data_source_read_csv_count - previous.data_source_read_csv_count
            regressions.append(f"read_csv_count increased by {delta}")

    # Contract error regressions
    if current.contract_error_count and previous.contract_error_count:
        if current.contract_error_count > previous.contract_error_count:
            delta = current.contract_error_count - previous.contract_error_count
            regressions.append(f"contract_error_count increased by {delta}")

    # Missing required artifacts
    if current.missing_required_count and previous.missing_required_count:
        if current.missing_required_count > previous.missing_required_count:
            delta = current.missing_required_count - previous.missing_required_count
            regressions.append(f"missing_required_count increased by {delta}")

    return regressions


def generate_history_summary_markdown(
    snapshots: list[BundleHistorySnapshot],
    last_n: int = 10,
) -> str:
    """Generate reviewer-friendly Markdown summary."""
    lines = [
        "# Validation Review Bundle History",
        "",
        "**Important**: This history summarizes offline Qlib research infrastructure validation bundles only. It is not a trading, execution, alpha, or model performance report.",
        "",
    ]

    if not snapshots:
        lines.append("No history snapshots available.")
        return "\n".join(lines)

    current = snapshots[-1]
    previous = snapshots[-2] if len(snapshots) > 1 else None

    lines.extend([
        "## Latest Bundle Status",
        "",
        f"- bundle_name: `{current.bundle_name}`",
        f"- created_at: `{current.created_at}`",
        f"- branch: `{current.branch}`",
        f"- commit: `{current.commit[:8] if len(current.commit) > 8 else current.commit}`",
        f"- delivery_packet_status: `{current.delivery_packet_status or 'N/A'}`",
        f"- runtime_budget_status: `{current.runtime_budget_status or 'N/A'}`",
        f"- fast_total: `{current.fast_total_seconds:.2f}s`" if current.fast_total_seconds else "- fast_total: N/A",
        "",
    ])

    if previous:
        delta = compute_delta(current, previous)
        regressions = detect_regressions(current, previous)

        lines.extend([
            "## Delta from Previous",
            "",
        ])

        if delta:
            for key, value in delta.items():
                if isinstance(value, float):
                    lines.append(f"- {key}: `{value:+.2f}`")
                else:
                    lines.append(f"- {key}: `{value}`")
        else:
            lines.append("No significant changes detected.")

        lines.append("")

        if regressions:
            lines.extend([
                "## ⚠️ Regressions Detected",
                "",
            ])
            for regression in regressions:
                lines.append(f"- {regression}")
            lines.append("")

    lines.extend([
        f"## Last {min(last_n, len(snapshots))} Snapshots",
        "",
        "| Created | Branch | Packet Status | Budget Status | Fast Total (s) | Read CSV |",
        "|---------|--------|---------------|---------------|----------------|----------|",
    ])

    for snapshot in snapshots[-last_n:]:
        created_short = snapshot.created_at[:19] if len(snapshot.created_at) > 19 else snapshot.created_at
        branch_short = snapshot.branch[:20] if len(snapshot.branch) > 20 else snapshot.branch
        packet_status = snapshot.delivery_packet_status or "N/A"
        budget_status = snapshot.runtime_budget_status or "N/A"
        fast_total = f"{snapshot.fast_total_seconds:.2f}" if snapshot.fast_total_seconds else "N/A"
        read_csv = str(snapshot.data_source_read_csv_count) if snapshot.data_source_read_csv_count else "N/A"

        lines.append(f"| {created_short} | {branch_short} | {packet_status} | {budget_status} | {fast_total} | {read_csv} |")

    lines.extend([
        "",
        "## Reviewer Recommendation",
        "",
    ])

    if previous:
        regressions = detect_regressions(current, previous)
        if regressions:
            lines.append("**Review regressions**: One or more validation metrics regressed. Review changes before merge.")
        elif current.runtime_budget_status == "pass" and current.delivery_packet_status in ("pass", "warn"):
            lines.append("**No action needed**: Validation state stable or improved.")
        else:
            lines.append("**Review warnings**: Check validation status before merge.")
    else:
        lines.append("**First snapshot**: No previous data for comparison.")

    lines.append("")
    return "\n".join(lines)
