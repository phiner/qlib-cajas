"""Post-removal closure report for history alias migration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_alias_post_removal_closure(
    *,
    review_bundle_manifest: Path,
    manifest_compatibility_report: Path,
    alias_fallback_removal_readiness: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    data_source_audit_report: Path,
) -> dict[str, Any]:
    manifest = _load_json(review_bundle_manifest)
    compatibility = _load_json(manifest_compatibility_report)
    fallback = _load_json(alias_fallback_removal_readiness)
    runtime_budget = _load_json(runtime_budget_report)
    runtime_edge = _load_json(runtime_edge_report)
    data_source_audit = _load_json(data_source_audit_report)

    canonical_only_manifest_confirmed = isinstance(manifest.get("history"), dict)
    history_update_absent = "history_update" not in manifest
    legacy_kept = fallback.get("legacy_read_normalization_kept") is True
    compatibility_status = compatibility.get("status", "fail")
    runtime_budget_status = runtime_budget.get("overall_status", "warn")
    runtime_edge_status = runtime_edge.get("status", "warn")
    timing_consistency_status = (runtime_budget.get("timing_consistency") or {}).get("status", "warn")
    read_csv_count = (data_source_audit.get("summary") or {}).get("read_csv_count", data_source_audit.get("read_csv_count"))

    blockers: list[str] = []
    followups: list[str] = []

    if not canonical_only_manifest_confirmed:
        blockers.append("canonical_history_missing")
    if not history_update_absent:
        blockers.append("history_update_still_present")
    if not legacy_kept:
        blockers.append("legacy_read_normalization_not_kept")
    if compatibility_status == "fail":
        blockers.append("manifest_compatibility_fail")
    elif compatibility_status == "warn":
        followups.append("manifest_compatibility_warn")
    if runtime_budget_status == "fail":
        blockers.append("runtime_budget_fail")
    elif runtime_budget_status == "warn":
        followups.append("runtime_budget_warn")
    if timing_consistency_status == "fail":
        blockers.append("timing_consistency_fail")
    elif timing_consistency_status == "warn":
        followups.append("timing_consistency_warn")
    if runtime_edge_status == "fail":
        blockers.append("runtime_edge_fail")
    elif runtime_edge_status in {"warn", "watch"}:
        followups.append(f"runtime_edge_{runtime_edge_status}")
    if not isinstance(read_csv_count, int):
        blockers.append("data_source_audit_missing_read_csv_count")

    if blockers:
        status = "blocked"
    elif followups:
        status = "watch"
    else:
        status = "closed"

    return {
        "schema_version": "v1",
        "status": status,
        "canonical_only_manifest_confirmed": canonical_only_manifest_confirmed,
        "history_update_absent": history_update_absent,
        "include_alias_flag_behavior": "fail_fast_deprecated",
        "omit_alias_flag_behavior": "noop_warning",
        "legacy_read_normalization_kept": legacy_kept,
        "manifest_compatibility_status": compatibility_status,
        "runtime_budget_status": runtime_budget_status,
        "timing_consistency_status": timing_consistency_status,
        "runtime_edge_status": runtime_edge_status,
        "data_source_audit_read_csv_count": read_csv_count,
        "release_readiness_status": "ready" if status == "closed" else ("blocked" if status == "blocked" else "watch"),
        "rollback_plan_present": bool(fallback.get("rollback_plan")),
        "remaining_followups": followups,
        "blocking_items": blockers,
        "non_goals": [
            "No trading execution",
            "No broker or order routing integration",
            "No live/paper trading workflow",
        ],
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_alias_post_removal_closure_markdown(payload: dict[str, Any]) -> str:
    blocking_items = payload.get("blocking_items", [])
    followups = payload.get("remaining_followups", [])
    return "\n".join(
        [
            "# Alias Post-Removal Closure",
            "",
            f"- Status: `{payload.get('status', 'watch')}`",
            f"- canonical_only_manifest_confirmed: `{payload.get('canonical_only_manifest_confirmed')}`",
            f"- history_update_absent: `{payload.get('history_update_absent')}`",
            f"- include_alias_flag_behavior: `{payload.get('include_alias_flag_behavior')}`",
            f"- omit_alias_flag_behavior: `{payload.get('omit_alias_flag_behavior')}`",
            f"- legacy_read_normalization_kept: `{payload.get('legacy_read_normalization_kept')}`",
            f"- manifest_compatibility_status: `{payload.get('manifest_compatibility_status')}`",
            f"- runtime_budget_status: `{payload.get('runtime_budget_status')}`",
            f"- timing_consistency_status: `{payload.get('timing_consistency_status')}`",
            f"- runtime_edge_status: `{payload.get('runtime_edge_status')}`",
            f"- data_source_audit_read_csv_count: `{payload.get('data_source_audit_read_csv_count')}`",
            f"- rollback_plan_present: `{payload.get('rollback_plan_present')}`",
            "",
            "## Blocking Items",
            "",
            *([f"- {x}" for x in blocking_items] if blocking_items else ["- none"]),
            "",
            "## Remaining Followups",
            "",
            *([f"- {x}" for x in followups] if followups else ["- none"]),
            "",
            "## Non-goals",
            "",
            *[f"- {x}" for x in payload.get("non_goals", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
