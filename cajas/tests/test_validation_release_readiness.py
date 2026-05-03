import json
from pathlib import Path

from cajas.reports.validation_release_readiness import (
    build_validation_release_readiness_report,
    render_validation_release_readiness_markdown,
)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _build_report(tmp_path: Path, *, alias_gate: str, runtime_variance: str = "pass", runtime_cycle: str = "pass") -> dict:
    milestone = _write_json(tmp_path / "milestone.json", {"overall_status": "watch", "alias_migration_summary": {"status": "pass"}})
    alias = _write_json(
        tmp_path / "alias.json",
        {"status": alias_gate, "decision_gate": {"status": alias_gate, "next_actions": ["collect_consumer_evidence"]}},
    )
    cycle = _write_json(tmp_path / "cycle.json", {"status": runtime_cycle})
    variance = _write_json(tmp_path / "variance.json", {"status": runtime_variance})
    edge = _write_json(tmp_path / "edge.json", {"status": "pass"})
    budget = _write_json(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}})
    removal = _write_json(tmp_path / "removal.json", {"status": "not_ready", "recommendation": "keep_fallback"})
    evidence = _write_json(tmp_path / "evidence_closure.json", {"status": "incomplete", "next_actions": ["identify_owner"]})
    handoff = _write_json(tmp_path / "owner_handoff.json", {"status": "open", "blocking_consumer_count": 1, "handoff_items": [{"consumer": "x", "next_action": "identify_owner"}]})
    owner_response = _write_json(tmp_path / "owner_response.json", {"status": "incomplete", "safe_to_update_evidence": False, "issues": ["missing_owner"]})
    candidate = _write_json(
        tmp_path / "candidate.json",
        {
            "status": "ready_candidate",
            "release_readiness_projected_status": "ready",
            "manual_approval_required": True,
            "next_action": "review_candidate_evidence",
        },
    )
    approval = _write_json(
        tmp_path / "approval_gate.json",
        {"status": "approval_required", "next_action": "manual_review_candidate"},
    )
    schedule = _write_json(
        tmp_path / "schedule.json",
        {"status": "not_scheduled", "reason": "manual_approval_required"},
    )
    update_plan = _write_json(
        tmp_path / "update_plan.json",
        {"status": "not_ready", "manual_update_required": True, "recommendation": "wait_for_approval"},
    )
    apply_report = _write_json(
        tmp_path / "apply_report.json",
        {"status": "dry_run_ready", "next_action": "manual_apply_in_dedicated_phase", "alias_fallback_removal_allowed": False},
    )
    applied_readiness = _write_json(
        tmp_path / "applied_readiness.json",
        {"status": "watch", "next_action": "resolve_applied_projection_gaps"},
    )
    fallback_removal = _write_json(
        tmp_path / "fallback_removal.json",
        {
            "status": "not_ready",
            "preconditions_met": False,
            "do_not_remove_in_this_phase": True,
            "fallback_removed": False,
            "active_alias_emission_supported": True,
            "legacy_read_normalization_kept": True,
            "post_removal_status": "watch",
        },
    )
    triage = _write_json(tmp_path / "runtime_triage.json", {"status": "watch", "recommendation": "profile_slow_tests"})
    profile = _write_json(
        tmp_path / "pytest_profile.json",
        {"status": "watch", "recommendation": "monitor", "test_summary": {"passed": 488, "deselected": 16}},
    )
    return build_validation_release_readiness_report(
        milestone_packet=milestone,
        alias_sunset_review=alias,
        runtime_release_cycle_report=cycle,
        runtime_variance_report=variance,
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        alias_removal_plan=removal,
        consumer_evidence_closure_report=evidence,
        consumer_owner_handoff=handoff,
        consumer_owner_response_validation=owner_response,
        consumer_evidence_candidate_report=candidate,
        evidence_candidate_approval_report=approval,
        alias_sunset_schedule=schedule,
        canonical_evidence_update_plan=update_plan,
        canonical_evidence_apply_report=apply_report,
        applied_evidence_readiness=applied_readiness,
        alias_fallback_removal_readiness=fallback_removal,
        runtime_watch_triage_report=triage,
        pytest_runtime_profile=profile,
    )


def test_release_readiness_watch_when_alias_watch(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="watch")
    assert report["status"] == "watch"
    assert "alias_sunset_decision_gate=watch" in report["watch_items"]


def test_release_readiness_blocked_when_alias_blocked(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="blocked")
    assert report["status"] == "blocked"
    assert "alias_sunset_decision_gate=blocked" in report["blocking_items"]


def test_release_readiness_watch_on_runtime_watch(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="ready", runtime_variance="watch")
    assert report["status"] == "watch"
    assert "runtime_variance_status=watch" in report["watch_items"]


def test_release_readiness_ready_when_all_green(tmp_path: Path) -> None:
    milestone = _write_json(
        tmp_path / "milestone.json",
        {"overall_status": "pass", "alias_migration_summary": {"status": "pass"}},
    )
    alias = _write_json(
        tmp_path / "alias.json",
        {"status": "ready", "decision_gate": {"status": "ready", "next_actions": ["schedule_removal"]}},
    )
    cycle = _write_json(tmp_path / "cycle.json", {"status": "pass"})
    variance = _write_json(tmp_path / "variance.json", {"status": "pass"})
    edge = _write_json(tmp_path / "edge.json", {"status": "pass"})
    budget = _write_json(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}})
    removal = _write_json(tmp_path / "removal.json", {"status": "ready_to_schedule", "recommendation": "schedule_removal_phase"})
    evidence = _write_json(tmp_path / "evidence_closure.json", {"status": "complete", "next_actions": []})
    handoff = _write_json(tmp_path / "owner_handoff.json", {"status": "ready", "blocking_consumer_count": 0, "handoff_items": []})
    owner_response = _write_json(tmp_path / "owner_response.json", {"status": "valid_ready_to_apply", "safe_to_update_evidence": True, "issues": []})
    candidate = _write_json(
        tmp_path / "candidate.json",
        {
            "status": "ready_candidate",
            "release_readiness_projected_status": "ready",
            "manual_approval_required": True,
            "next_action": "review_candidate_evidence",
        },
    )
    approval = _write_json(
        tmp_path / "approval_gate.json",
        {"status": "approved_candidate", "next_action": "apply_in_dedicated_phase"},
    )
    schedule = _write_json(
        tmp_path / "schedule.json",
        {"status": "ready_to_schedule", "reason": "approved_candidate_and_removal_plan_ready"},
    )
    update_plan = _write_json(
        tmp_path / "update_plan.json",
        {"status": "ready_to_apply", "manual_update_required": True, "recommendation": "apply_in_dedicated_phase"},
    )
    apply_report = _write_json(
        tmp_path / "apply_report.json",
        {"status": "dry_run_ready", "next_action": "manual_apply_in_dedicated_phase", "alias_fallback_removal_allowed": False},
    )
    applied_readiness = _write_json(
        tmp_path / "applied_readiness.json",
        {"status": "ready_for_real_apply", "next_action": "perform_real_apply_in_dedicated_phase_or_schedule_alias_removal_review"},
    )
    fallback_removal = _write_json(
        tmp_path / "fallback_removal.json",
        {
            "status": "ready_to_schedule",
            "preconditions_met": True,
            "do_not_remove_in_this_phase": False,
            "fallback_removed": True,
            "active_alias_emission_supported": False,
            "legacy_read_normalization_kept": True,
            "post_removal_status": "pass",
        },
    )
    triage = _write_json(tmp_path / "runtime_triage.json", {"status": "pass", "recommendation": "monitor"})
    profile = _write_json(
        tmp_path / "pytest_profile.json",
        {"status": "watch", "recommendation": "monitor", "test_summary": {"passed": 488, "deselected": 16}},
    )
    report = build_validation_release_readiness_report(
        milestone_packet=milestone,
        alias_sunset_review=alias,
        runtime_release_cycle_report=cycle,
        runtime_variance_report=variance,
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        alias_removal_plan=removal,
        consumer_evidence_closure_report=evidence,
        consumer_owner_handoff=handoff,
        consumer_owner_response_validation=owner_response,
        consumer_evidence_candidate_report=candidate,
        evidence_candidate_approval_report=approval,
        alias_sunset_schedule=schedule,
        canonical_evidence_update_plan=update_plan,
        canonical_evidence_apply_report=apply_report,
        applied_evidence_readiness=applied_readiness,
        alias_fallback_removal_readiness=fallback_removal,
        runtime_watch_triage_report=triage,
        pytest_runtime_profile=profile,
    )
    assert report["status"] == "ready"
    md = render_validation_release_readiness_markdown(report)
    assert "Next Actions" in md
    assert "Scope Boundary" in md


def test_release_readiness_includes_alias_removal_plan_summary(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="watch")
    assert report["alias_removal_plan_status"] == "not_ready"
    assert "alias_removal_plan_status=not_ready" in report["watch_items"]
    assert report["consumer_evidence_closure_status"] == "incomplete"
    assert report["runtime_watch_triage_status"] == "watch"
    assert report["consumer_evidence_action_plan"] == []
    assert report["pytest_runtime_profile_status"] == "watch"
    assert report["consumer_owner_handoff_status"] == "open"
    assert report["consumer_owner_response_status"] == "incomplete"
    assert report["consumer_evidence_candidate_status"] == "ready_candidate"
    assert report["evidence_candidate_approval_status"] == "approval_required"
    assert report["alias_sunset_schedule_status"] == "not_scheduled"
    assert report["canonical_evidence_update_plan_status"] == "not_ready"
    assert report["canonical_evidence_apply_report_status"] == "dry_run_ready"
    assert report["applied_evidence_readiness_status"] == "watch"
    assert report["alias_fallback_removal_readiness_status"] == "not_ready"
    assert report["fallback_removed"] is False


def test_post_removal_mode_supersedes_pre_removal_watch_items(tmp_path: Path) -> None:
    milestone = _write_json(tmp_path / "milestone.json", {"overall_status": "watch", "alias_migration_summary": {"status": "pass"}})
    alias = _write_json(tmp_path / "alias.json", {"status": "watch", "decision_gate": {"status": "watch", "next_actions": ["collect_consumer_evidence"]}})
    cycle = _write_json(tmp_path / "cycle.json", {"status": "pass"})
    variance = _write_json(tmp_path / "variance.json", {"status": "pass"})
    edge = _write_json(tmp_path / "edge.json", {"status": "pass"})
    budget = _write_json(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}})
    removal = _write_json(tmp_path / "removal.json", {"status": "not_ready"})
    evidence = _write_json(tmp_path / "evidence_closure.json", {"status": "incomplete"})
    handoff = _write_json(tmp_path / "owner_handoff.json", {"status": "open"})
    owner_response = _write_json(tmp_path / "owner_response.json", {"status": "incomplete"})
    candidate = _write_json(tmp_path / "candidate.json", {"status": "ready_candidate"})
    approval = _write_json(tmp_path / "approval.json", {"status": "approval_required"})
    schedule = _write_json(tmp_path / "schedule.json", {"status": "not_scheduled"})
    update_plan = _write_json(tmp_path / "update_plan.json", {"status": "not_ready"})
    apply_report = _write_json(tmp_path / "apply_report.json", {"status": "dry_run_ready"})
    applied_readiness = _write_json(tmp_path / "applied_readiness.json", {"status": "ready_for_real_apply"})
    fallback = _write_json(
        tmp_path / "fallback.json",
        {
            "status": "ready_to_schedule",
            "fallback_removed": True,
            "active_alias_emission_supported": False,
            "legacy_read_normalization_kept": True,
            "post_removal_status": "pass",
        },
    )
    closure = _write_json(tmp_path / "closure.json", {"status": "closed", "release_readiness_status": "ready"})
    report = build_validation_release_readiness_report(
        milestone_packet=milestone,
        alias_sunset_review=alias,
        runtime_release_cycle_report=cycle,
        runtime_variance_report=variance,
        runtime_edge_report=edge,
        runtime_budget_report=budget,
        alias_removal_plan=removal,
        consumer_evidence_closure_report=evidence,
        consumer_owner_handoff=handoff,
        consumer_owner_response_validation=owner_response,
        consumer_evidence_candidate_report=candidate,
        evidence_candidate_approval_report=approval,
        alias_sunset_schedule=schedule,
        canonical_evidence_update_plan=update_plan,
        canonical_evidence_apply_report=apply_report,
        applied_evidence_readiness=applied_readiness,
        alias_fallback_removal_readiness=fallback,
        alias_post_removal_closure=closure,
    )
    assert report["status"] == "ready"
    assert report["post_removal_mode"] is True
    assert report["release_ready_after_post_removal"] is True
    assert "alias_sunset_decision_gate=watch" in report["superseded_watch_items"]
    assert not report["remaining_watch_items"]


def test_post_removal_runtime_fail_still_blocks(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="ready")
    # Rebuild with runtime fail and post-removal closure
    _write_json(tmp_path / "budget.json", {"overall_status": "fail", "timing_consistency": {"status": "pass"}})
    _write_json(
        tmp_path / "fallback_removal.json",
        {
            "status": "ready_to_schedule",
            "fallback_removed": True,
            "active_alias_emission_supported": False,
            "legacy_read_normalization_kept": True,
            "post_removal_status": "pass",
        },
    )
    _write_json(tmp_path / "closure.json", {"status": "closed", "release_readiness_status": "ready"})
    blocked = build_validation_release_readiness_report(
        milestone_packet=tmp_path / "milestone.json",
        alias_sunset_review=tmp_path / "alias.json",
        runtime_release_cycle_report=tmp_path / "cycle.json",
        runtime_variance_report=tmp_path / "variance.json",
        runtime_edge_report=tmp_path / "edge.json",
        runtime_budget_report=tmp_path / "budget.json",
        alias_removal_plan=tmp_path / "removal.json",
        consumer_evidence_closure_report=tmp_path / "evidence_closure.json",
        consumer_owner_handoff=tmp_path / "owner_handoff.json",
        consumer_owner_response_validation=tmp_path / "owner_response.json",
        consumer_evidence_candidate_report=tmp_path / "candidate.json",
        evidence_candidate_approval_report=tmp_path / "approval_gate.json",
        alias_sunset_schedule=tmp_path / "schedule.json",
        canonical_evidence_update_plan=tmp_path / "update_plan.json",
        canonical_evidence_apply_report=tmp_path / "apply_report.json",
        applied_evidence_readiness=tmp_path / "applied_readiness.json",
        alias_fallback_removal_readiness=tmp_path / "fallback_removal.json",
        runtime_watch_triage_report=tmp_path / "runtime_triage.json",
        pytest_runtime_profile=tmp_path / "pytest_profile.json",
        alias_post_removal_closure=tmp_path / "closure.json",
    )
    assert blocked["status"] == "blocked"
    assert "runtime_budget_status=fail" in blocked["blocking_items"]


def test_release_readiness_includes_final_closure_fields(tmp_path: Path) -> None:
    report = _build_report(tmp_path, alias_gate="ready")
    _write_json(tmp_path / "release_ready_closure.json", {"status": "watch", "recommendation": "monitor_runtime_next_cycle"})
    payload = build_validation_release_readiness_report(
        milestone_packet=tmp_path / "milestone.json",
        alias_sunset_review=tmp_path / "alias.json",
        runtime_release_cycle_report=tmp_path / "cycle.json",
        runtime_variance_report=tmp_path / "variance.json",
        runtime_edge_report=tmp_path / "edge.json",
        runtime_budget_report=tmp_path / "budget.json",
        alias_removal_plan=tmp_path / "removal.json",
        consumer_evidence_closure_report=tmp_path / "evidence_closure.json",
        consumer_owner_handoff=tmp_path / "owner_handoff.json",
        consumer_owner_response_validation=tmp_path / "owner_response.json",
        consumer_evidence_candidate_report=tmp_path / "candidate.json",
        evidence_candidate_approval_report=tmp_path / "approval_gate.json",
        alias_sunset_schedule=tmp_path / "schedule.json",
        canonical_evidence_update_plan=tmp_path / "update_plan.json",
        canonical_evidence_apply_report=tmp_path / "apply_report.json",
        applied_evidence_readiness=tmp_path / "applied_readiness.json",
        alias_fallback_removal_readiness=tmp_path / "fallback_removal.json",
        runtime_watch_triage_report=tmp_path / "runtime_triage.json",
        pytest_runtime_profile=tmp_path / "pytest_profile.json",
        release_ready_closure=tmp_path / "release_ready_closure.json",
    )
    assert payload["release_ready_closure_status"] == "watch"
