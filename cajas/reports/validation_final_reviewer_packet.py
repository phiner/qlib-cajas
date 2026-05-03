"""Final reviewer packet report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_final_reviewer_packet(
    *,
    release_ready_closure: Path,
    alias_post_removal_closure: Path,
    runtime_variance_closure: Path,
    release_readiness_report: Path,
    milestone_packet: Path,
    review_bundle_manifest: Path,
    manifest_compatibility_report: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    data_source_audit_report: Path,
    maintenance_cadence: Path | None = None,
    maintenance_checklist: Path | None = None,
    optional_followups: Path | None = None,
) -> dict[str, Any]:
    final_closure = _load_json(release_ready_closure)
    alias_closure = _load_json(alias_post_removal_closure)
    variance_closure = _load_json(runtime_variance_closure)
    readiness = _load_json(release_readiness_report)
    milestone = _load_json(milestone_packet)
    manifest = _load_json(review_bundle_manifest)
    compat = _load_json(manifest_compatibility_report)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)
    audit = _load_json(data_source_audit_report)
    cadence = _load_json(maintenance_cadence) if maintenance_cadence and maintenance_cadence.exists() else {}
    checklist = _load_json(maintenance_checklist) if maintenance_checklist and maintenance_checklist.exists() else {}
    followups_queue = _load_json(optional_followups) if optional_followups and optional_followups.exists() else {}

    canonical_only = isinstance(manifest.get("history"), dict) and "history_update" not in manifest
    legacy_kept = readiness.get("legacy_read_normalization_kept") is True
    read_csv_count = (audit.get("summary") or {}).get("read_csv_count", audit.get("read_csv_count"))

    summary = {
        "canonical_only_manifest": canonical_only,
        "alias_post_removal_closure": alias_closure.get("status"),
        "legacy_read_normalization_kept": legacy_kept,
        "manifest_compatibility": compat.get("status"),
        "runtime_budget": budget.get("overall_status"),
        "runtime_edge": edge.get("status"),
        "runtime_variance_closure": variance_closure.get("status"),
        "data_source_audit_read_csv_count": read_csv_count,
    }

    blockers: list[str] = []
    followups: list[str] = []

    if final_closure.get("blocking") is True or final_closure.get("status") == "blocked":
        blockers.extend(final_closure.get("remaining_blockers", []))
    if compat.get("status") == "fail":
        blockers.append("manifest_compatibility_fail")
    if budget.get("overall_status") == "fail":
        blockers.append("runtime_budget_fail")
    if edge.get("status") == "fail":
        blockers.append("runtime_edge_fail")
    if not canonical_only:
        blockers.append("canonical_manifest_missing_or_alias_present")
    if not legacy_kept:
        blockers.append("legacy_read_normalization_not_kept")

    if variance_closure.get("status") == "monitoring_only":
        followups.append("monitor runtime variance next release cycle")
    followups.extend(final_closure.get("remaining_followups", []))
    followups = sorted(set(followups))

    if blockers:
        status = "blocked"
    elif final_closure.get("ready_for_review") is True:
        status = "ready_for_review"
    else:
        status = "watch"

    return {
        "schema_version": "v1",
        "status": status,
        "summary": summary,
        "maintenance_cadence_status": cadence.get("status"),
        "maintenance_cadence_recommended": cadence.get("recommended_cadence"),
        "maintenance_cadence_routine_commands": cadence.get("routine_commands", []),
        "maintenance_cadence_watch_items": cadence.get("watch_items", []),
        "maintenance_checklist_status": checklist.get("status"),
        "maintenance_checklist_mode": checklist.get("mode"),
        "maintenance_checklist_canonical_artifacts": checklist.get("canonical_artifacts", []),
        "optional_followups_status": followups_queue.get("status"),
        "optional_followups_count": len(followups_queue.get("items", [])),
        "optional_followups_blocking": followups_queue.get("blocking", False),
        "remaining_followups": followups,
        "primary_artifacts": [
            str(release_ready_closure),
            str(release_readiness_report),
            str(milestone_packet),
            str(review_bundle_manifest),
            str(manifest_compatibility_report),
        ],
        "rollback_readiness": "present" if alias_closure.get("status") == "closed" else "unknown",
        "non_goals": [
            "No trading execution",
            "No broker integration",
            "No live/paper execution",
        ],
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_final_reviewer_packet_markdown(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    return "\n".join(
        [
            "# Validation Final Reviewer Packet",
            "",
            f"- Status: `{payload.get('status')}`",
            f"- canonical_only_manifest: `{s.get('canonical_only_manifest')}`",
            f"- alias_post_removal_closure: `{s.get('alias_post_removal_closure')}`",
            f"- legacy_read_normalization_kept: `{s.get('legacy_read_normalization_kept')}`",
            f"- manifest_compatibility: `{s.get('manifest_compatibility')}`",
            f"- runtime_budget: `{s.get('runtime_budget')}`",
            f"- runtime_edge: `{s.get('runtime_edge')}`",
            f"- runtime_variance_closure: `{s.get('runtime_variance_closure')}`",
            f"- data_source_audit_read_csv_count: `{s.get('data_source_audit_read_csv_count')}`",
            "",
            "## Remaining Followups",
            "",
            *([f"- {x}" for x in payload.get("remaining_followups", [])] if payload.get("remaining_followups") else ["- none"]),
            "",
            "## Maintenance Cadence",
            "",
            f"- status: `{payload.get('maintenance_cadence_status', 'not_included')}`",
            f"- recommended_cadence: `{payload.get('maintenance_cadence_recommended', 'n/a')}`",
            f"- routine_command_count: `{len(payload.get('maintenance_cadence_routine_commands', []))}`",
            f"- watch_items: `{payload.get('maintenance_cadence_watch_items', [])}`",
            "",
            "## Maintenance Checklist",
            "",
            f"- status: `{payload.get('maintenance_checklist_status', 'not_included')}`",
            f"- mode: `{payload.get('maintenance_checklist_mode', 'n/a')}`",
            f"- canonical_artifact_count: `{len(payload.get('maintenance_checklist_canonical_artifacts', []))}`",
            "",
            "## Optional Followup Queue",
            "",
            f"- status: `{payload.get('optional_followups_status', 'not_included')}`",
            f"- count: `{payload.get('optional_followups_count', 0)}`",
            f"- blocking: `{payload.get('optional_followups_blocking', False)}`",
            "",
            "## Reviewer Handoff",
            "",
            f"- Status: `{'Ready for review' if payload.get('status') == 'ready_for_review' else payload.get('status')}`",
            "- Canonical manifest policy: `history-only`",
            f"- Alias migration: `{s.get('alias_post_removal_closure')}`",
            f"- Runtime: `budget={s.get('runtime_budget')}; edge={s.get('runtime_edge')}; variance_closure={s.get('runtime_variance_closure')}`",
            f"- Data-source audit: `stable at {s.get('data_source_audit_read_csv_count')} read_csv calls`",
            f"- Next routine action: `run maintenance cadence at {payload.get('maintenance_cadence_recommended', 'next release cycle')}`",
            "",
            "## Primary Artifacts",
            "",
            *[f"- `{x}`" for x in payload.get("primary_artifacts", [])],
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
