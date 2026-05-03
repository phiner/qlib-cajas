"""Final release-ready closure report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_release_ready_closure(
    *,
    alias_post_removal_closure: Path,
    release_readiness_report: Path,
    milestone_packet: Path,
    runtime_release_cycle_report: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    manifest_compatibility_report: Path,
    data_source_audit_report: Path,
    review_bundle_manifest: Path,
) -> dict[str, Any]:
    alias_closure = _load_json(alias_post_removal_closure)
    readiness = _load_json(release_readiness_report)
    milestone = _load_json(milestone_packet)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    runtime_budget = _load_json(runtime_budget_report)
    runtime_edge = _load_json(runtime_edge_report)
    manifest_compat = _load_json(manifest_compatibility_report)
    audit = _load_json(data_source_audit_report)
    manifest = _load_json(review_bundle_manifest)

    alias_status = alias_closure.get("status")
    readiness_status = readiness.get("status")
    milestone_status = milestone.get("overall_status")
    runtime_cycle_status = runtime_cycle.get("status")
    runtime_budget_status = runtime_budget.get("overall_status")
    runtime_edge_status = runtime_edge.get("status")
    manifest_compat_status = manifest_compat.get("status")
    read_csv_count = (audit.get("summary") or {}).get("read_csv_count", audit.get("read_csv_count"))

    canonical_only_manifest_confirmed = isinstance(manifest.get("history"), dict) and "history_update" not in manifest
    legacy_read_normalization_kept = readiness.get("legacy_read_normalization_kept") is True

    remaining_blockers: list[str] = []
    remaining_followups: list[str] = []

    if alias_status != "closed":
        remaining_blockers.append(f"alias_post_removal_closure_status={alias_status}")
    if manifest_compat_status == "fail":
        remaining_blockers.append("manifest_compatibility_status=fail")
    elif manifest_compat_status == "warn":
        remaining_followups.append("manifest_compatibility_status=warn")
    if runtime_budget_status == "fail":
        remaining_blockers.append("runtime_budget_status=fail")
    elif runtime_budget_status == "warn":
        remaining_followups.append("runtime_budget_status=warn")
    if runtime_edge_status == "fail":
        remaining_blockers.append("runtime_edge_status=fail")
    elif runtime_edge_status in {"warn", "watch"}:
        remaining_followups.append(f"runtime_edge_status={runtime_edge_status}")
    if runtime_cycle_status == "fail":
        remaining_blockers.append("runtime_release_cycle_status=fail")
    elif runtime_cycle_status in {"warn", "watch"}:
        remaining_followups.append(f"runtime_release_cycle_status={runtime_cycle_status}")
    if not canonical_only_manifest_confirmed:
        remaining_blockers.append("canonical_only_manifest_not_confirmed")
    if not legacy_read_normalization_kept:
        remaining_blockers.append("legacy_read_normalization_not_kept")
    if not isinstance(read_csv_count, int):
        remaining_blockers.append("data_source_audit_read_csv_count_missing")

    if remaining_blockers:
        status = "blocked"
        recommendation = "resolve_blockers"
    elif remaining_followups:
        status = "watch"
        recommendation = "monitor_runtime_next_cycle"
    else:
        status = "ready"
        recommendation = "ready_for_review"

    return {
        "schema_version": "v1",
        "status": status,
        "alias_post_removal_closure_status": alias_status,
        "release_readiness_status": readiness_status,
        "milestone_status": milestone_status,
        "runtime_release_cycle_status": runtime_cycle_status,
        "runtime_budget_status": runtime_budget_status,
        "runtime_edge_status": runtime_edge_status,
        "manifest_compatibility_status": manifest_compat_status,
        "data_source_audit_read_csv_count": read_csv_count,
        "canonical_only_manifest_confirmed": canonical_only_manifest_confirmed,
        "legacy_read_normalization_kept": legacy_read_normalization_kept,
        "remaining_blockers": remaining_blockers,
        "remaining_followups": remaining_followups,
        "recommendation": recommendation,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_release_ready_closure_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Release-Ready Closure",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- Alias post-removal closure: `{payload.get('alias_post_removal_closure_status')}`",
            f"- Release readiness: `{payload.get('release_readiness_status')}`",
            f"- Milestone status: `{payload.get('milestone_status')}`",
            f"- Runtime release-cycle: `{payload.get('runtime_release_cycle_status')}`",
            f"- Runtime budget: `{payload.get('runtime_budget_status')}`",
            f"- Runtime edge: `{payload.get('runtime_edge_status')}`",
            f"- Manifest compatibility: `{payload.get('manifest_compatibility_status')}`",
            f"- data_source_audit_read_csv_count: `{payload.get('data_source_audit_read_csv_count')}`",
            f"- canonical_only_manifest_confirmed: `{payload.get('canonical_only_manifest_confirmed')}`",
            f"- legacy_read_normalization_kept: `{payload.get('legacy_read_normalization_kept')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "",
            "## Remaining Blockers",
            "",
            *([f"- {x}" for x in payload.get("remaining_blockers", [])] if payload.get("remaining_blockers") else ["- none"]),
            "",
            "## Remaining Followups",
            "",
            *([f"- {x}" for x in payload.get("remaining_followups", [])] if payload.get("remaining_followups") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
