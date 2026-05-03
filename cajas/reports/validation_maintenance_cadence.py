"""Maintenance cadence report for post-milestone routine validation."""

from __future__ import annotations

import json
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


def build_validation_maintenance_cadence_report(
    *,
    release_readiness_report: Path,
    release_ready_closure: Path,
    final_reviewer_packet: Path,
    alias_post_removal_closure: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    runtime_release_cycle_report: Path,
    data_source_audit_report: Path,
) -> dict[str, Any]:
    readiness = _load_json(release_readiness_report)
    closure = _load_json(release_ready_closure)
    reviewer = _load_json(final_reviewer_packet)
    alias_closure = _load_json(alias_post_removal_closure)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    audit = _load_json(data_source_audit_report)

    release_ready = readiness.get("status") == "ready"
    closure_ready = closure.get("status") == "ready" and closure.get("ready_for_review") is True
    reviewer_ready = reviewer.get("status") == "ready_for_review"
    alias_closed = alias_closure.get("status") == "closed"
    runtime_ok = (
        budget.get("overall_status") == "pass"
        and (budget.get("timing_consistency") or {}).get("status") == "pass"
        and edge.get("status") == "pass"
        and runtime_cycle.get("status") == "pass"
    )

    blockers: list[str] = []
    if budget.get("overall_status") == "fail":
        blockers.append("runtime_budget_status=fail")
    if (budget.get("timing_consistency") or {}).get("status") == "fail":
        blockers.append("timing_consistency_status=fail")
    if edge.get("status") == "fail":
        blockers.append("runtime_edge_status=fail")
    if runtime_cycle.get("status") == "fail":
        blockers.append("runtime_release_cycle_status=fail")
    if closure.get("blocking") is True or closure.get("status") == "blocked":
        blockers.append("release_ready_closure_status=blocked")
    if readiness.get("status") == "blocked":
        blockers.append("release_readiness_status=blocked")
    if reviewer.get("status") == "blocked":
        blockers.append("final_reviewer_packet_status=blocked")

    watch_items: list[str] = []
    if runtime_cycle.get("status") in {"watch", "warn"}:
        watch_items.append(f"runtime_release_cycle_status={runtime_cycle.get('status')}")
    if edge.get("status") in {"watch", "warn"}:
        watch_items.append(f"runtime_edge_status={edge.get('status')}")
    if readiness.get("status") == "watch":
        watch_items.append("release_readiness_status=watch")
    if reviewer.get("status") == "watch":
        watch_items.append("final_reviewer_packet_status=watch")
    watch_items.extend(closure.get("non_blocking_followups", []))
    watch_items = sorted(set(watch_items))

    if blockers:
        status = "blocked"
    elif release_ready and closure_ready and reviewer_ready and alias_closed and runtime_ok and not watch_items:
        status = "routine"
    else:
        status = "active"

    return {
        "schema_version": "v1",
        "status": status,
        "recommended_cadence": "next_release_cycle",
        "routine_commands": [
            "cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json",
            "cajas/scripts/check_validation_runtime_budget.py --budgets cajas/data_examples/validation_runtime_budgets.json --timing-json tmp/fast_validation_latest.json --out-json tmp/validation_runtime_budget_report.json --out-md tmp/validation_runtime_budget_report.md",
            "cajas/scripts/build_validation_runtime_edge_report.py --timing-json tmp/fast_validation_latest.json --runtime-budget-report tmp/validation_runtime_budget_report.json --out-json tmp/validation-runtime-edge-report.json --out-md tmp/validation-runtime-edge-report.md",
            "cajas/scripts/build_validation_runtime_release_cycle_report.py --runtime-edge-report tmp/validation-runtime-edge-report.json --runtime-budget-report tmp/validation_runtime_budget_report.json --fast-timing-json tmp/fast_validation_latest.json --runtime-variance-report tmp/validation-runtime-variance-report.json --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json --out-json tmp/validation-runtime-release-cycle-report.json --out-md tmp/validation-runtime-release-cycle-report.md",
            "cajas/scripts/audit_data_sources.py --project-root cajas --data-root /tmp/nonexistent-data-root-for-static-audit --out-json tmp/data_source_audit.json --out-md tmp/data_source_audit.md",
            "cajas/scripts/build_validation_final_reviewer_packet.py --release-ready-closure tmp/validation-release-ready-closure.json --alias-post-removal-closure tmp/alias-post-removal-closure.json --runtime-variance-closure tmp/validation-runtime-variance-closure.json --release-readiness-report tmp/validation-release-readiness.json --milestone-packet tmp/validation-milestone-packet.json --review-bundle-manifest tmp/validation-review-bundle/review_bundle_manifest.json --manifest-compatibility-report tmp/validation-review-bundle/manifest_compatibility_report.json --runtime-budget-report tmp/validation_runtime_budget_report.json --runtime-edge-report tmp/validation-runtime-edge-report.json --data-source-audit-report tmp/data_source_audit.json --maintenance-cadence tmp/validation-maintenance-cadence.json --out-json tmp/validation-final-reviewer-packet.json --out-md tmp/validation-final-reviewer-packet.md",
        ],
        "watch_items": watch_items,
        "blocking_reasons": blockers,
        "rollback_readiness": "preserved" if alias_closed else "unknown",
        "canonical_manifest_policy": "history_only",
        "legacy_read_normalization": "kept" if readiness.get("legacy_read_normalization_kept") is True else "unknown",
        "data_source_audit_expected_read_csv_count": _read_csv_count(audit),
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_maintenance_cadence_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Maintenance Cadence",
            "",
            f"- Status: `{payload.get('status')}`",
            f"- recommended_cadence: `{payload.get('recommended_cadence')}`",
            f"- rollback_readiness: `{payload.get('rollback_readiness')}`",
            f"- canonical_manifest_policy: `{payload.get('canonical_manifest_policy')}`",
            f"- legacy_read_normalization: `{payload.get('legacy_read_normalization')}`",
            f"- data_source_audit_expected_read_csv_count: `{payload.get('data_source_audit_expected_read_csv_count')}`",
            "",
            "## Routine Commands",
            "",
            *[f"- `{x}`" for x in payload.get("routine_commands", [])],
            "",
            "## Watch Items",
            "",
            *([f"- {x}" for x in payload.get("watch_items", [])] if payload.get("watch_items") else ["- none"]),
            "",
            "## Blocking Reasons",
            "",
            *([f"- {x}" for x in payload.get("blocking_reasons", [])] if payload.get("blocking_reasons") else ["- none"]),
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
