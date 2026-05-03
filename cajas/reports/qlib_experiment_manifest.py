"""Qlib experiment reproducibility manifest."""

from __future__ import annotations

import datetime
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class QlibExperimentManifest:
    """Qlib experiment reproducibility manifest."""

    manifest_version: str
    created_at: str
    experiment_name: str
    dataset_path: str | None
    dataset_quality_report_path: str | None
    contract_report_path: str | None
    trend_snapshot_path: str | None
    golden_scenario_manifest_path: str | None
    qlib_config_path: str | None
    git_branch: str | None
    git_commit: str | None
    python_version: str
    platform_info: str
    notes: str | None


def get_git_info() -> tuple[str | None, str | None]:
    """Get git branch and commit."""
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.DEVNULL, text=True).strip()
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        return branch or None, commit or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None


def build_qlib_experiment_manifest(
    experiment_name: str,
    dataset_path: str | None = None,
    dataset_quality_report_path: str | None = None,
    contract_report_path: str | None = None,
    trend_snapshot_path: str | None = None,
    golden_scenario_manifest_path: str | None = None,
    qlib_config_path: str | None = None,
    notes: str | None = None,
    created_at: str | None = None,
) -> QlibExperimentManifest:
    """Build Qlib experiment manifest."""
    git_branch, git_commit = get_git_info()

    return QlibExperimentManifest(
        manifest_version="v1",
        created_at=created_at or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        experiment_name=experiment_name,
        dataset_path=dataset_path,
        dataset_quality_report_path=dataset_quality_report_path,
        contract_report_path=contract_report_path,
        trend_snapshot_path=trend_snapshot_path,
        golden_scenario_manifest_path=golden_scenario_manifest_path,
        qlib_config_path=qlib_config_path,
        git_branch=git_branch,
        git_commit=git_commit,
        python_version=sys.version,
        platform_info=platform.platform(),
        notes=notes,
    )


def validate_qlib_experiment_manifest(manifest: QlibExperimentManifest) -> list[str]:
    """Validate Qlib experiment manifest."""
    errors = []

    if not manifest.experiment_name:
        errors.append("experiment_name is required")

    # Check referenced paths exist
    path_fields = [
        ("dataset_path", manifest.dataset_path),
        ("dataset_quality_report_path", manifest.dataset_quality_report_path),
        ("contract_report_path", manifest.contract_report_path),
        ("trend_snapshot_path", manifest.trend_snapshot_path),
        ("golden_scenario_manifest_path", manifest.golden_scenario_manifest_path),
        ("qlib_config_path", manifest.qlib_config_path),
    ]

    for field_name, path_str in path_fields:
        if path_str:
            path = Path(path_str)
            if not path.exists():
                errors.append(f"{field_name} does not exist: {path_str}")
            elif field_name.endswith("_path") and path_str.endswith(".json"):
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as e:
                    errors.append(f"{field_name} is not valid JSON: {e}")

    return errors


def manifest_to_dict(manifest: QlibExperimentManifest) -> dict:
    """Convert manifest to dict."""
    return {
        "manifest_version": manifest.manifest_version,
        "created_at": manifest.created_at,
        "experiment_name": manifest.experiment_name,
        "dataset_path": manifest.dataset_path,
        "dataset_quality_report_path": manifest.dataset_quality_report_path,
        "contract_report_path": manifest.contract_report_path,
        "trend_snapshot_path": manifest.trend_snapshot_path,
        "golden_scenario_manifest_path": manifest.golden_scenario_manifest_path,
        "qlib_config_path": manifest.qlib_config_path,
        "git_branch": manifest.git_branch,
        "git_commit": manifest.git_commit,
        "python_version": manifest.python_version,
        "platform_info": manifest.platform_info,
        "notes": manifest.notes,
    }


def generate_manifest_markdown(manifest: QlibExperimentManifest, manifest_dict: dict) -> str:
    """Generate reviewer-friendly Markdown report."""
    lines = [
        "# Qlib Experiment Reproducibility Manifest",
        "",
        "**Important**: This manifest is for offline Qlib research reproducibility only. It is not a trading execution artifact.",
        "",
        f"- experiment_name: `{manifest.experiment_name}`",
        f"- manifest_version: `{manifest.manifest_version}`",
        f"- created_at: `{manifest.created_at}`",
        "",
        "## Reproducibility Status",
        "",
    ]

    # Read dataset quality status if available
    dq_status = "unknown"
    dq_score = "unknown"
    if manifest.dataset_quality_report_path:
        dq_path = Path(manifest.dataset_quality_report_path)
        if dq_path.exists():
            try:
                dq_report = json.loads(dq_path.read_text(encoding="utf-8"))
                dq_status = dq_report.get("status", "unknown")
                dq_score = dq_report.get("quality_score", {}).get("score", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass

    # Read contract status if available
    contract_status = "unknown"
    semantic_error_count = "unknown"
    drift_breaking_count = "unknown"
    if manifest.contract_report_path:
        contract_path = Path(manifest.contract_report_path)
        if contract_path.exists():
            try:
                contract_report = json.loads(contract_path.read_text(encoding="utf-8"))
                contract_status = contract_report.get("status", "unknown")
                semantic_error_count = contract_report.get("semantic_error_count", "unknown")
                drift_breaking_count = contract_report.get("drift_summary", {}).get("breaking_count", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass

    # Read trend snapshot if available
    trend_quality_score = "unknown"
    trend_quality_grade = "unknown"
    if manifest.trend_snapshot_path:
        trend_path = Path(manifest.trend_snapshot_path)
        if trend_path.exists():
            try:
                trend_snapshot = json.loads(trend_path.read_text(encoding="utf-8"))
                trend_quality_score = trend_snapshot.get("quality_score", "unknown")
                trend_quality_grade = trend_snapshot.get("quality_grade", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass

    lines.extend([
        f"- dataset_quality_status: `{dq_status}`",
        f"- dataset_quality_score: `{dq_score}`",
        f"- contract_status: `{contract_status}`",
        f"- semantic_error_count: `{semantic_error_count}`",
        f"- drift_breaking_count: `{drift_breaking_count}`",
        f"- trend_quality_score: `{trend_quality_score}`",
        f"- trend_quality_grade: `{trend_quality_grade}`",
        "",
        "## Source Information",
        "",
        f"- dataset_path: `{manifest.dataset_path or 'not specified'}`",
        f"- git_branch: `{manifest.git_branch or 'unknown'}`",
        f"- git_commit: `{manifest.git_commit or 'unknown'}`",
        f"- python_version: `{manifest.python_version.split()[0]}`",
        f"- platform: `{manifest.platform_info}`",
        "",
        "## Referenced Artifacts",
        "",
        "| Artifact | Path | Status |",
        "|----------|------|--------|",
    ])

    artifacts = [
        ("Dataset", manifest.dataset_path),
        ("Dataset Quality Report", manifest.dataset_quality_report_path),
        ("Contract Report", manifest.contract_report_path),
        ("Trend Snapshot", manifest.trend_snapshot_path),
        ("Golden Scenario Manifest", manifest.golden_scenario_manifest_path),
        ("Qlib Config", manifest.qlib_config_path),
    ]

    for name, path in artifacts:
        if path:
            exists = "✅" if Path(path).exists() else "❌"
            lines.append(f"| {name} | `{path}` | {exists} |")
        else:
            lines.append(f"| {name} | not specified | - |")

    lines.extend([
        "",
        "## Reviewer Notes",
        "",
    ])

    if contract_status == "pass" and dq_status in ("pass", "warn"):
        lines.append("**Status**: Reproducibility artifacts are present and validated.")
    elif contract_status == "fail" or semantic_error_count != 0:
        lines.append("**Action required**: Contract validation failed or semantic errors detected.")
    else:
        lines.append("**Status**: Partial reproducibility information available.")

    if manifest.notes:
        lines.extend([
            "",
            "## Additional Notes",
            "",
            manifest.notes,
        ])

    lines.append("")
    return "\n".join(lines)
