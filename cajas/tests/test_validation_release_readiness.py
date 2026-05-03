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
