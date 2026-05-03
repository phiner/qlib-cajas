"""Routine release-cycle stability report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PASS_STATES = {"pass", "ready", "ready_for_review", "closed", "sealed", "healthy", "routine", "stable"}
WATCH_STATES = {"watch", "warn", "active", "monitoring_only", "open", "ready_candidate"}
BLOCK_STATES = {"fail", "blocked", "error", "invalid"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return _load_json(path)


def _read_csv_count(audit: dict[str, Any]) -> int | None:
    direct = audit.get("read_csv_count")
    if isinstance(direct, int):
        return direct
    nested = (audit.get("summary") or {}).get("read_csv_count")
    if isinstance(nested, int):
        return nested
    return None


def _to_bool(value: Any) -> bool:
    return value is True


def _classify(status: Any) -> str:
    if isinstance(status, str):
        normalized = status.lower()
        if normalized in BLOCK_STATES:
            return "block"
        if normalized in WATCH_STATES:
            return "watch"
        if normalized in PASS_STATES:
            return "pass"
    return "unknown"


def build_validation_routine_release_cycle_stability(
    *,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    milestone_packet: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    runtime_release_cycle_report: Path,
    runtime_variance_closure_report: Path,
    data_source_audit_report: Path,
    path_hygiene_report: Path | None = None,
    maintenance_checklist: Path | None = None,
    maintenance_governance_closure: Path | None = None,
    final_maintenance_archive_closure_report: Path | None = None,
    external_consumer_evidence_closure_report: Path | None = None,
    post_freeze_handoff_seal_report: Path | None = None,
    optional_followups: Path | None = None,
) -> dict[str, Any]:
    readiness = _load_json(release_readiness_report)
    reviewer = _load_json(final_reviewer_packet)
    milestone = _load_json(milestone_packet)
    runtime_budget = _load_json(runtime_budget_report)
    runtime_edge = _load_json(runtime_edge_report)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    runtime_variance = _load_json(runtime_variance_closure_report)
    audit = _load_json(data_source_audit_report)

    checklist = _load_optional(maintenance_checklist)
    governance = _load_optional(maintenance_governance_closure)
    archive = _load_optional(final_maintenance_archive_closure_report)
    external = _load_optional(external_consumer_evidence_closure_report)
    handoff = _load_optional(post_freeze_handoff_seal_report)
    hygiene = _load_optional(path_hygiene_report)
    followups = _load_optional(optional_followups)

    checks: list[dict[str, Any]] = []
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []

    def add_check(name: str, status: Any, blocking: bool | None = None, detail: str | None = None) -> None:
        state = _classify(status)
        entry = {
            "name": name,
            "status": status,
            "state": state,
            "blocking": bool(blocking) if blocking is not None else False,
        }
        if detail:
            entry["detail"] = detail
        checks.append(entry)
        if state == "block" or entry["blocking"]:
            blocking_reasons.append(f"{name}={status}")
        elif state in {"watch", "unknown"}:
            watch_reasons.append(f"{name}={status}")

    add_check("release_readiness", readiness.get("status"), readiness.get("status") == "blocked")
    add_check("final_reviewer_packet", reviewer.get("status"), reviewer.get("status") == "blocked")
    add_check("milestone_review_state", milestone.get("review_state"), _to_bool(milestone.get("blocking")))
    add_check("maintenance_checklist", checklist.get("status") if checklist else "not_included")
    add_check("maintenance_governance_closure", governance.get("status") if governance else "not_included")
    add_check("final_maintenance_archive_closure", archive.get("status") if archive else "not_included", _to_bool(archive.get("blocking")))
    add_check("external_consumer_evidence_closure", external.get("status") if external else "not_included", _to_bool(external.get("blocking")))
    add_check("post_freeze_handoff_seal", handoff.get("status") if handoff else "not_included", _to_bool(handoff.get("blocking")))
    add_check("runtime_budget", runtime_budget.get("overall_status"), runtime_budget.get("overall_status") == "fail")
    add_check(
        "timing_consistency",
        (runtime_budget.get("timing_consistency") or {}).get("status"),
        (runtime_budget.get("timing_consistency") or {}).get("status") == "fail",
    )
    add_check("runtime_edge", runtime_edge.get("status"), runtime_edge.get("status") == "fail")
    add_check("runtime_release_cycle", runtime_cycle.get("status"), runtime_cycle.get("status") == "fail")
    add_check("runtime_variance_closure", runtime_variance.get("status"), runtime_variance.get("status") == "fail")
    add_check("path_hygiene", hygiene.get("status") if hygiene else "not_included")

    followup_items = followups.get("active_items", followups.get("items", [])) if followups else []
    followup_count = len(followup_items) if isinstance(followup_items, list) else 0
    followup_blocking = bool(followups.get("blocking", False)) if followups else False
    followup_status = followups.get("status", "not_included") if followups else "not_included"
    add_check("optional_followups", followup_status, followup_blocking)

    read_csv_count = _read_csv_count(audit)

    summary = {
        "release_readiness_status": readiness.get("status"),
        "final_reviewer_packet_status": reviewer.get("status"),
        "milestone_review_state": milestone.get("review_state"),
        "milestone_blocking": bool(milestone.get("blocking")),
        "maintenance_checklist_status": checklist.get("status"),
        "maintenance_governance_closure_status": governance.get("status"),
        "final_maintenance_archive_closure_status": archive.get("status"),
        "external_consumer_evidence_closure_status": external.get("status"),
        "post_freeze_handoff_seal_status": handoff.get("status"),
        "runtime_budget_status": runtime_budget.get("overall_status"),
        "timing_consistency_status": (runtime_budget.get("timing_consistency") or {}).get("status"),
        "runtime_edge_status": runtime_edge.get("status"),
        "runtime_release_cycle_status": runtime_cycle.get("status"),
        "runtime_variance_closure_status": runtime_variance.get("status"),
        "path_hygiene_status": hygiene.get("status"),
        "data_source_audit_read_csv_count": read_csv_count,
        "optional_followups_status": followup_status,
        "optional_followups_count": followup_count,
        "optional_followups_blocking": followup_blocking,
    }

    required_ready = (
        readiness.get("status") == "ready"
        and reviewer.get("status") == "ready_for_review"
        and milestone.get("review_state") == "ready_for_review"
        and not bool(milestone.get("blocking"))
        and runtime_budget.get("overall_status") == "pass"
        and (runtime_budget.get("timing_consistency") or {}).get("status") == "pass"
        and runtime_edge.get("status") == "pass"
        and runtime_cycle.get("status") == "pass"
        and runtime_variance.get("status") in {"closed", "pass"}
        and (not checklist or checklist.get("status") in {"ready", "pass"})
        and (not governance or governance.get("status") in {"ready", "pass"})
        and (not archive or archive.get("status") in {"ready", "closed", "pass"})
        and (not external or external.get("status") in {"closed", "ready", "closed_unresolved_external", "pass"})
        and (not handoff or handoff.get("status") in {"sealed", "ready", "pass"})
        and (not hygiene or hygiene.get("status") in {"pass", "ready", "clean"})
    )

    if blocking_reasons:
        status = "blocked"
    elif required_ready and followup_count > 0 and not followup_blocking:
        status = "watch"
    elif required_ready:
        status = "stable"
    elif watch_reasons:
        status = "watch"
    else:
        status = "blocked"

    review_state = "ready_for_review" if status in {"stable", "watch"} and not blocking_reasons and not followup_blocking else "blocked"
    blocking = bool(blocking_reasons or followup_blocking)

    next_actions: list[str] = []
    if status == "blocked":
        next_actions.append("resolve_blocking_validation_gates")
    elif status == "watch":
        next_actions.append("complete_non_blocking_followups_next_release_cycle")
    else:
        next_actions.append("continue_routine_release_cycle_validation")

    return {
        "schema_version": 1,
        "status": status,
        "review_state": review_state,
        "blocking": blocking,
        "recommended_cadence": "next_release_cycle",
        "summary": summary,
        "checks": checks,
        "remaining_followups": sorted(set(watch_reasons + [f"optional_followups_count={followup_count}"] if followup_count else watch_reasons)),
        "next_actions": sorted(set(next_actions)),
    }


def render_validation_routine_release_cycle_stability_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Routine Release-Cycle Stability",
            "",
            f"- status: `{payload.get('status')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- blocking: `{payload.get('blocking')}`",
            f"- recommended_cadence: `{payload.get('recommended_cadence')}`",
            "",
            "## Summary",
            "",
            *[f"- {k}: `{v}`" for k, v in (payload.get("summary") or {}).items()],
            "",
            "## Checks",
            "",
            *[
                f"- {item.get('name')}: status=`{item.get('status')}` state=`{item.get('state')}` blocking=`{item.get('blocking')}`"
                for item in payload.get("checks", [])
            ],
            "",
            "## Remaining Followups",
            "",
            *([f"- {item}" for item in payload.get("remaining_followups", [])] if payload.get("remaining_followups") else ["- none"]),
            "",
            "## Next Actions",
            "",
            *([f"- {item}" for item in payload.get("next_actions", [])] if payload.get("next_actions") else ["- none"]),
            "",
        ]
    )
