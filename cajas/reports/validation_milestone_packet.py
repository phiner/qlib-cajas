"""Phase 2000+ milestone packet report builder."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_count(audit: dict[str, Any]) -> int | None:
    direct = audit.get("read_csv_count")
    if isinstance(direct, int):
        return direct
    nested = (audit.get("summary") or {}).get("read_csv_count")
    if isinstance(nested, int):
        return nested
    return None


def _gate_overall_from_final_status(final_status: dict[str, Any]) -> str:
    overall = final_status.get("overall_status")
    return overall if isinstance(overall, str) else "warn"


def _build_artifact_map(
    *,
    review_bundle_root: Path,
    alias_fallback_bundle_root: Path,
    runtime_edge_report: Path,
    migration_readiness_report: Path,
    runtime_budget_report: Path,
    data_source_audit_report: Path,
    fast_timing_json: Path,
) -> dict[str, str]:
    return {
        "default_review_bundle_index_md": str(review_bundle_root / "review_bundle_index.md"),
        "default_final_status_json": str(review_bundle_root / "final_status.json"),
        "default_final_status_md": str(review_bundle_root / "final_status.md"),
        "default_review_bundle_manifest_json": str(review_bundle_root / "review_bundle_manifest.json"),
        "default_profile_matrix_json": str(review_bundle_root / "profile_matrix.json"),
        "default_profile_matrix_md": str(review_bundle_root / "profile_matrix.md"),
        "default_delivery_packet_manifest_json": str(review_bundle_root / "delivery_packet" / "packet_manifest.json"),
        "default_manifest_compatibility_json": str(review_bundle_root / "manifest_compatibility_report.json"),
        "default_manifest_compatibility_md": str(review_bundle_root / "manifest_compatibility_report.md"),
        "default_history_summary_json": str(review_bundle_root / "history" / "review_bundle_history_summary.json"),
        "default_history_summary_md": str(review_bundle_root / "history" / "review_bundle_history_summary.md"),
        "alias_fallback_review_bundle_manifest_json": str(alias_fallback_bundle_root / "review_bundle_manifest.json"),
        "alias_fallback_final_status_json": str(alias_fallback_bundle_root / "final_status.json"),
        "alias_fallback_profile_matrix_json": str(alias_fallback_bundle_root / "profile_matrix.json"),
        "runtime_budget_report_json": str(runtime_budget_report),
        "runtime_edge_report_json": str(runtime_edge_report),
        "migration_readiness_report_json": str(migration_readiness_report),
        "data_source_audit_report_json": str(data_source_audit_report),
        "fast_timing_json": str(fast_timing_json),
    }


def build_validation_milestone_packet(
    *,
    review_bundle_root: Path,
    alias_fallback_bundle_root: Path,
    runtime_edge_report: Path,
    migration_readiness_report: Path,
    runtime_budget_report: Path,
    data_source_audit_report: Path,
    fast_timing_json: Path,
    alias_sunset_review: Path | None = None,
    runtime_release_cycle_report: Path | None = None,
    runtime_variance_report: Path | None = None,
    release_readiness_report: Path | None = None,
    alias_removal_plan: Path | None = None,
    consumer_evidence_closure_report: Path | None = None,
    consumer_owner_handoff: Path | None = None,
    runtime_watch_triage_report: Path | None = None,
    pytest_runtime_profile: Path | None = None,
) -> dict[str, Any]:
    default_final = _load_json(review_bundle_root / "final_status.json")
    alias_final = _load_json(alias_fallback_bundle_root / "final_status.json")
    default_matrix = _load_json(review_bundle_root / "profile_matrix.json")
    runtime_edge = _load_json(runtime_edge_report)
    migration = _load_json(migration_readiness_report)
    runtime_budget = _load_json(runtime_budget_report)
    data_source_audit = _load_json(data_source_audit_report)
    fast_timing = _load_json(fast_timing_json)
    alias_sunset = _load_json(alias_sunset_review) if alias_sunset_review and alias_sunset_review.exists() else None
    runtime_release_cycle = (
        _load_json(runtime_release_cycle_report)
        if runtime_release_cycle_report and runtime_release_cycle_report.exists()
        else None
    )
    runtime_variance = _load_json(runtime_variance_report) if runtime_variance_report and runtime_variance_report.exists() else None
    release_readiness = (
        _load_json(release_readiness_report) if release_readiness_report and release_readiness_report.exists() else None
    )
    removal_plan = _load_json(alias_removal_plan) if alias_removal_plan and alias_removal_plan.exists() else None
    evidence_closure = (
        _load_json(consumer_evidence_closure_report)
        if consumer_evidence_closure_report and consumer_evidence_closure_report.exists()
        else None
    )
    owner_handoff = _load_json(consumer_owner_handoff) if consumer_owner_handoff and consumer_owner_handoff.exists() else None
    runtime_watch_triage = (
        _load_json(runtime_watch_triage_report)
        if runtime_watch_triage_report and runtime_watch_triage_report.exists()
        else None
    )
    runtime_profile = _load_json(pytest_runtime_profile) if pytest_runtime_profile and pytest_runtime_profile.exists() else None

    default_overall = _gate_overall_from_final_status(default_final)
    alias_overall = _gate_overall_from_final_status(alias_final)
    runtime_edge_status = runtime_edge.get("status", "warn")
    migration_status = migration.get("status", "warn")

    alias_sunset_status = (alias_sunset or {}).get("status")
    runtime_cycle_status = (runtime_release_cycle or {}).get("status")
    runtime_variance_status = (runtime_variance or {}).get("status")
    release_readiness_status = (release_readiness or {}).get("status")

    if default_overall == "fail" or alias_overall == "fail":
        overall_status = "fail"
    elif alias_sunset_status in {"watch", "blocked"}:
        overall_status = "watch"
    elif migration_status in {"warn", "fail"}:
        overall_status = "warn"
    elif runtime_cycle_status in {"watch", "warn", "fail"}:
        overall_status = runtime_cycle_status
    elif runtime_variance_status in {"watch", "warn", "fail"}:
        overall_status = runtime_variance_status
    elif release_readiness_status in {"watch", "blocked"}:
        overall_status = "watch" if release_readiness_status == "watch" else "fail"
    elif runtime_edge_status == "watch":
        overall_status = "watch"
    elif runtime_edge_status == "fail":
        overall_status = "fail"
    elif runtime_edge_status == "warn":
        overall_status = "warn"
    else:
        overall_status = "pass"

    gate_summary = {
        "default_bundle_overall": default_overall,
        "alias_fallback_bundle_overall": alias_overall,
        "runtime_budget_status": runtime_budget.get("overall_status"),
        "timing_consistency_status": (runtime_budget.get("timing_consistency") or {}).get("status"),
        "runtime_edge_status": runtime_edge_status,
        "migration_readiness_status": migration_status,
    }

    profile_summary = {
        "default_bundle_profiles": {
            k: v.get("overall_status") for k, v in (default_matrix.get("profiles") or {}).items()
        }
    }

    runtime_summary = {
        "fast_total_seconds": fast_timing.get("total_seconds"),
        "runtime_budget_overall_status": runtime_budget.get("overall_status"),
        "timing_consistency_status": (runtime_budget.get("timing_consistency") or {}).get("status"),
        "runtime_edge": runtime_edge,
    }

    recent_phase_summary = [
        "Phase 1886-1945: alias deprecation metadata and canonical-only mode option (~86.781s fast validation baseline).",
        "Phase 1946-2005: no-alias migration readiness pass (~92.92s baseline).",
        "Phase 2006-2065: default no-alias trial with explicit fallback (~93.681s baseline).",
        "Phase 2066-2125: runtime edge report added (~84.861s baseline).",
    ]

    risks: list[str] = []
    if migration_status != "pass":
        risks.append("Alias migration readiness is not pass; fallback sunset should be deferred.")
    if runtime_edge_status in {"watch", "warn", "fail"}:
        risks.append("Runtime is near or beyond edge threshold; monitor variance.")
    if not risks:
        risks.append("External downstream consumers may still require explicit alias fallback during migration window.")

    recommended_next_actions = [
        "Keep canonical-only default manifest behavior.",
        "Maintain explicit alias fallback for external consumers until next sunset review.",
        "Track runtime edge trend per release cycle and investigate drift if watch/warn reappears.",
        "Prepare a follow-up sunset decision phase with external consumer confirmation evidence.",
    ]

    return {
        "schema_version": "v1",
        "milestone": "phase_2000_plus_validation_automation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall_status,
        "current_baseline": {
            "default_manifest_mode": "canonical_history_only",
            "fallback_flag": "--include-history-update-alias",
            "transition_flag": "--omit-history-update-alias",
        },
        "artifact_map": _build_artifact_map(
            review_bundle_root=review_bundle_root,
            alias_fallback_bundle_root=alias_fallback_bundle_root,
            runtime_edge_report=runtime_edge_report,
            migration_readiness_report=migration_readiness_report,
            runtime_budget_report=runtime_budget_report,
            data_source_audit_report=data_source_audit_report,
            fast_timing_json=fast_timing_json,
        ),
        "gate_summary": gate_summary,
        "profile_summary": profile_summary,
        "runtime_summary": runtime_summary,
        "runtime_release_cycle_summary": runtime_release_cycle,
        "runtime_variance_summary": runtime_variance,
        "release_readiness_summary": release_readiness,
        "alias_removal_plan_summary": removal_plan,
        "consumer_evidence_closure_summary": evidence_closure,
        "consumer_owner_handoff_summary": owner_handoff,
        "runtime_watch_triage_summary": runtime_watch_triage,
        "pytest_runtime_profile_summary": runtime_profile,
        "alias_migration_summary": migration,
        "alias_sunset_review_summary": alias_sunset,
        "data_source_audit_summary": {
            "read_csv_count": _read_csv_count(data_source_audit),
        },
        "recent_phase_summary": recent_phase_summary,
        "risks": risks,
        "recommended_next_actions": recommended_next_actions,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_milestone_packet_markdown(payload: dict[str, Any]) -> str:
    artifact_map = payload.get("artifact_map", {})
    return "\n".join(
        [
            "# Qlib Base Validation Automation Milestone Packet",
            "",
            "## Overall Status",
            "",
            f"- `{payload.get('overall_status', 'warn')}`",
            "",
            "## Current Operating Model",
            "",
            "- Default manifest emits canonical `history` only.",
            "- Deprecated alias fallback is explicit via `--include-history-update-alias`.",
            "",
            "## Primary Reviewer Artifacts",
            "",
            f"1. `{artifact_map.get('default_review_bundle_index_md', '')}`",
            f"2. `{artifact_map.get('default_final_status_md', '')}`",
            f"3. `{artifact_map.get('default_profile_matrix_md', '')}`",
            f"4. `{artifact_map.get('runtime_edge_report_json', '')}`",
            f"5. `{artifact_map.get('migration_readiness_report_json', '')}`",
            "",
            "## CI/Profile Matrix Summary",
            "",
            f"- `{payload.get('profile_summary', {})}`",
            "",
            "## Runtime Budget and Runtime Edge",
            "",
            f"- `{payload.get('runtime_summary', {})}`",
            "",
            "## History Alias Migration Status",
            "",
            f"- `{payload.get('alias_migration_summary', {}).get('status', 'warn')}`",
            "",
            "## Alias Sunset Review",
            "",
            f"- `{(payload.get('alias_sunset_review_summary') or {}).get('status', 'not_included')}`",
            f"- action: `{(payload.get('alias_sunset_review_summary') or {}).get('recommended_action', 'n/a')}`",
            "",
            "## Data Source Audit",
            "",
            f"- read_csv_count: `{(payload.get('data_source_audit_summary') or {}).get('read_csv_count')}`",
            "",
            "## Recent Phase Summary",
            "",
            *[f"- {item}" for item in payload.get("recent_phase_summary", [])],
            "",
            "## Remaining Risks",
            "",
            *[f"- {item}" for item in payload.get("risks", [])],
            "",
            "## Recommended Next Actions",
            "",
            *[f"- {item}" for item in payload.get("recommended_next_actions", [])],
            "",
            "## Runtime Release-Cycle Monitor",
            "",
            f"- `{(payload.get('runtime_release_cycle_summary') or {}).get('status', 'not_included')}`",
            f"- next trigger: `{(payload.get('runtime_release_cycle_summary') or {}).get('next_review_trigger', 'n/a')}`",
            "",
            "## Runtime Variance Triage",
            "",
            f"- `{(payload.get('runtime_variance_summary') or {}).get('status', 'not_included')}`",
            f"- recommendation: `{(payload.get('runtime_variance_summary') or {}).get('recommendation', 'n/a')}`",
            "",
            "## Release Readiness Dashboard",
            "",
            f"- `{(payload.get('release_readiness_summary') or {}).get('status', 'not_included')}`",
            f"- reason: `{(payload.get('release_readiness_summary') or {}).get('release_readiness_reason', 'n/a')}`",
            f"- next_actions: `{(payload.get('release_readiness_summary') or {}).get('next_actions', [])}`",
            "",
            "## Alias Removal Plan",
            "",
            f"- `{(payload.get('alias_removal_plan_summary') or {}).get('status', 'not_included')}`",
            f"- preconditions_met: `{(payload.get('alias_removal_plan_summary') or {}).get('preconditions_met', 'n/a')}`",
            f"- recommendation: `{(payload.get('alias_removal_plan_summary') or {}).get('recommendation', 'n/a')}`",
            f"- remaining_blockers: `{(payload.get('alias_removal_plan_summary') or {}).get('remaining_blockers', [])}`",
            "",
            "## Consumer Evidence Closure",
            "",
            f"- `{(payload.get('consumer_evidence_closure_summary') or {}).get('status', 'not_included')}`",
            f"- next_actions: `{(payload.get('consumer_evidence_closure_summary') or {}).get('next_actions', [])}`",
            f"- action_plan: `{(payload.get('consumer_evidence_closure_summary') or {}).get('action_plan', [])}`",
            "",
            "## Runtime Watch Triage",
            "",
            f"- `{(payload.get('runtime_watch_triage_summary') or {}).get('status', 'not_included')}`",
            f"- recommendation: `{(payload.get('runtime_watch_triage_summary') or {}).get('recommendation', 'n/a')}`",
            f"- test_count: `{(payload.get('runtime_watch_triage_summary') or {}).get('test_count', 'n/a')}`",
            f"- seconds_per_test: `{(payload.get('runtime_watch_triage_summary') or {}).get('seconds_per_test', 'n/a')}`",
            "",
            "## Consumer Owner Handoff",
            "",
            f"- `{(payload.get('consumer_owner_handoff_summary') or {}).get('status', 'not_included')}`",
            f"- blocking_consumer_count: `{(payload.get('consumer_owner_handoff_summary') or {}).get('blocking_consumer_count', 'n/a')}`",
            f"- handoff_items: `{(payload.get('consumer_owner_handoff_summary') or {}).get('handoff_items', [])}`",
            "",
            "## Pytest Runtime Profile",
            "",
            f"- `{(payload.get('pytest_runtime_profile_summary') or {}).get('status', 'not_included')}`",
            f"- recommendation: `{(payload.get('pytest_runtime_profile_summary') or {}).get('recommendation', 'n/a')}`",
            f"- test_summary: `{(payload.get('pytest_runtime_profile_summary') or {}).get('test_summary', {})}`",
            f"- slowest_tests_count: `{len((payload.get('pytest_runtime_profile_summary') or {}).get('slowest_tests', []))}`",
            f"- slowest_files_count: `{len((payload.get('pytest_runtime_profile_summary') or {}).get('slowest_files', []))}`",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
