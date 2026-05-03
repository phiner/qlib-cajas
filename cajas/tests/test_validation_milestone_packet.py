import json
from pathlib import Path

from cajas.reports.validation_milestone_packet import (
    build_validation_milestone_packet,
    render_validation_milestone_packet_markdown,
)
from cajas.scripts.build_validation_milestone_packet import main as milestone_main


def _write_bundle(root: Path, *, overall: str = "pass") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "final_status.json").write_text(json.dumps({"overall_status": overall}), encoding="utf-8")
    (root / "profile_matrix.json").write_text(
        json.dumps({"profiles": {"local": {"overall_status": "pass"}, "ci": {"overall_status": "pass"}, "strict": {"overall_status": "warn"}}}),
        encoding="utf-8",
    )
    (root / "review_bundle_index.md").write_text("# idx", encoding="utf-8")
    (root / "final_status.md").write_text("# final", encoding="utf-8")
    (root / "review_bundle_manifest.json").write_text(json.dumps({"manifest_compatibility": {"status": "pass"}}), encoding="utf-8")
    (root / "delivery_packet").mkdir(parents=True, exist_ok=True)
    (root / "delivery_packet" / "packet_manifest.json").write_text(json.dumps({"overall_status": "pass"}), encoding="utf-8")


def _write_common_inputs(tmp_path: Path) -> dict[str, Path]:
    default = tmp_path / "default"
    alias = tmp_path / "alias-fallback"
    _write_bundle(default, overall="pass")
    _write_bundle(alias, overall="pass")
    (tmp_path / "runtime-edge.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (tmp_path / "migration.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (tmp_path / "runtime-budget.json").write_text(
        json.dumps({"overall_status": "pass", "timing_consistency": {"status": "pass"}, "results": []}),
        encoding="utf-8",
    )
    (tmp_path / "audit.json").write_text(json.dumps({"summary": {"read_csv_count": 29}}), encoding="utf-8")
    (tmp_path / "timing.json").write_text(json.dumps({"total_seconds": 84.0}), encoding="utf-8")
    return {
        "default": default,
        "alias": alias,
        "runtime_edge": tmp_path / "runtime-edge.json",
        "migration": tmp_path / "migration.json",
        "runtime_budget": tmp_path / "runtime-budget.json",
        "audit": tmp_path / "audit.json",
        "timing": tmp_path / "timing.json",
    }


def test_milestone_packet_build_pass(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )
    assert packet["overall_status"] == "pass"
    assert "artifact_map" in packet
    assert packet["current_baseline"]["active_alias_emission_supported"] is False
    md = render_validation_milestone_packet_markdown(packet)
    assert "Scope Boundary" in md
    assert "Primary Reviewer Artifacts" in md


def test_milestone_packet_watch_status(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    (p["runtime_edge"]).write_text(json.dumps({"status": "watch"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )
    assert packet["overall_status"] == "watch"


def test_milestone_packet_includes_optional_alias_and_runtime_cycle(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    alias_sunset = tmp_path / "alias_sunset.json"
    runtime_cycle = tmp_path / "runtime_cycle.json"
    alias_sunset.write_text(json.dumps({"status": "watch", "recommended_action": "keep_fallback"}), encoding="utf-8")
    runtime_cycle.write_text(json.dumps({"status": "watch", "next_review_trigger": "remaining_budget_ratio_below_0.15"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_sunset_review=alias_sunset,
        runtime_release_cycle_report=runtime_cycle,
    )
    assert packet["alias_sunset_review_summary"]["status"] == "watch"
    assert packet["runtime_release_cycle_summary"]["status"] == "watch"


def test_milestone_packet_includes_runtime_variance_and_watch_reason(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    alias_sunset = tmp_path / "alias_sunset.json"
    runtime_cycle = tmp_path / "runtime_cycle.json"
    runtime_variance = tmp_path / "runtime_variance.json"
    alias_sunset.write_text(json.dumps({"status": "watch", "recommended_action": "keep_fallback"}), encoding="utf-8")
    runtime_cycle.write_text(json.dumps({"status": "pass", "next_review_trigger": "manual_next_release"}), encoding="utf-8")
    runtime_variance.write_text(json.dumps({"status": "watch", "recommendation": "watch_next_cycle"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_sunset_review=alias_sunset,
        runtime_release_cycle_report=runtime_cycle,
        runtime_variance_report=runtime_variance,
    )
    assert packet["runtime_variance_summary"]["status"] == "watch"
    assert packet["overall_status"] == "watch"


def test_milestone_packet_includes_release_readiness_summary(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    release_readiness = tmp_path / "release_readiness.json"
    release_readiness.write_text(
        json.dumps(
            {
                "status": "watch",
                "release_readiness_reason": "alias_sunset_decision_gate=watch",
                "next_actions": ["collect_consumer_evidence", "keep_fallback"],
            }
        ),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        release_readiness_report=release_readiness,
    )
    assert packet["release_readiness_summary"]["status"] == "watch"
    md = render_validation_milestone_packet_markdown(packet)
    assert "Release Readiness Dashboard" in md


def test_milestone_packet_includes_alias_removal_plan_summary(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    removal_plan = tmp_path / "removal_plan.json"
    removal_plan.write_text(
        json.dumps(
            {
                "status": "not_ready",
                "preconditions_met": False,
                "recommendation": "keep_fallback",
                "remaining_blockers": ["alias_sunset_status=watch"],
            }
        ),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_removal_plan=removal_plan,
    )
    assert packet["alias_removal_plan_summary"]["status"] == "not_ready"
    md = render_validation_milestone_packet_markdown(packet)
    assert "Alias Removal Plan" in md


def test_milestone_packet_includes_evidence_closure_and_runtime_triage(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    evidence = tmp_path / "evidence.json"
    triage = tmp_path / "triage.json"
    evidence.write_text(
        json.dumps({"status": "incomplete", "next_actions": ["identify_owner"], "action_plan": [{"consumer": "x", "owner": "external-review-needed"}]}),
        encoding="utf-8",
    )
    triage.write_text(
        json.dumps({"status": "watch", "recommendation": "profile_slow_tests", "test_count": 486, "seconds_per_test": 0.18}),
        encoding="utf-8",
    )
    pytest_profile = tmp_path / "pytest_profile.json"
    pytest_profile.write_text(
        json.dumps(
            {
                "status": "watch",
                "recommendation": "monitor",
                "test_summary": {"passed": 488, "deselected": 16},
                "slowest_tests": [{"nodeid": "cajas/tests/test_a.py::test_x", "seconds": 2.1}],
                "slowest_files": [{"file": "cajas/tests/test_a.py", "total_seconds": 2.1, "test_count": 1}],
            }
        ),
        encoding="utf-8",
    )
    owner_handoff = tmp_path / "owner_handoff.json"
    owner_handoff.write_text(
        json.dumps(
            {
                "status": "open",
                "blocking_consumer_count": 1,
                "handoff_items": [{"consumer": "x", "owner": "external-review-needed", "next_action": "identify_owner"}],
            }
        ),
        encoding="utf-8",
    )
    owner_response = tmp_path / "owner_response.json"
    owner_response.write_text(
        json.dumps({"status": "incomplete", "safe_to_update_evidence": False, "issues": ["missing_owner"]}),
        encoding="utf-8",
    )
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(
            {
                "status": "ready_candidate",
                "release_readiness_projected_status": "ready",
                "manual_approval_required": True,
            }
        ),
        encoding="utf-8",
    )
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "status": "approval_required",
                "next_action": "manual_review_candidate",
                "manual_approval_required": True,
            }
        ),
        encoding="utf-8",
    )
    schedule = tmp_path / "schedule.json"
    schedule.write_text(
        json.dumps(
            {
                "status": "not_scheduled",
                "reason": "manual_approval_required",
                "do_not_remove_in_this_phase": True,
            }
        ),
        encoding="utf-8",
    )
    update_plan = tmp_path / "update_plan.json"
    update_plan.write_text(
        json.dumps(
            {
                "status": "not_ready",
                "recommendation": "wait_for_approval",
                "manual_update_required": True,
            }
        ),
        encoding="utf-8",
    )
    apply_report = tmp_path / "apply_report.json"
    apply_report.write_text(
        json.dumps(
            {
                "status": "dry_run_ready",
                "next_action": "manual_apply_in_dedicated_phase",
                "alias_fallback_removal_allowed": False,
            }
        ),
        encoding="utf-8",
    )
    applied_readiness = tmp_path / "applied_readiness.json"
    applied_readiness.write_text(
        json.dumps(
            {
                "status": "watch",
                "next_action": "resolve_applied_projection_gaps",
            }
        ),
        encoding="utf-8",
    )
    fallback_removal = tmp_path / "fallback_removal.json"
    fallback_removal.write_text(
        json.dumps(
            {
                "status": "not_ready",
                "preconditions_met": False,
                "do_not_remove_in_this_phase": True,
            }
        ),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        consumer_evidence_closure_report=evidence,
        consumer_owner_handoff=owner_handoff,
        consumer_owner_response_validation=owner_response,
        consumer_evidence_candidate_report=candidate,
        evidence_candidate_approval_report=approval,
        alias_sunset_schedule=schedule,
        canonical_evidence_update_plan=update_plan,
        canonical_evidence_apply_report=apply_report,
        applied_evidence_readiness=applied_readiness,
        alias_fallback_removal_readiness=fallback_removal,
        runtime_watch_triage_report=triage,
        pytest_runtime_profile=pytest_profile,
    )
    assert packet["consumer_evidence_closure_summary"]["status"] == "incomplete"
    assert packet["runtime_watch_triage_summary"]["status"] == "watch"
    assert packet["consumer_owner_handoff_summary"]["status"] == "open"
    assert packet["consumer_owner_response_validation_summary"]["status"] == "incomplete"
    assert packet["consumer_evidence_candidate_summary"]["status"] == "ready_candidate"
    assert packet["evidence_candidate_approval_summary"]["status"] == "approval_required"
    assert packet["alias_sunset_schedule_summary"]["status"] == "not_scheduled"
    assert packet["canonical_evidence_update_plan_summary"]["status"] == "not_ready"
    assert packet["canonical_evidence_apply_report_summary"]["status"] == "dry_run_ready"
    assert packet["applied_evidence_readiness_summary"]["status"] == "watch"
    assert packet["alias_fallback_removal_readiness_summary"]["status"] == "not_ready"
    assert packet["pytest_runtime_profile_summary"]["status"] == "watch"
    md = render_validation_milestone_packet_markdown(packet)
    assert "Consumer Evidence Closure" in md
    assert "Runtime Watch Triage" in md
    assert "Consumer Owner Handoff" in md
    assert "Consumer Owner Response Validation" in md
    assert "Consumer Evidence Candidate" in md
    assert "Evidence Candidate Approval Gate" in md
    assert "Alias Sunset Schedule" in md
    assert "Canonical Evidence Update Plan" in md
    assert "Canonical Evidence Apply Report" in md
    assert "Applied Evidence Readiness" in md
    assert "Alias Fallback Removal Readiness" in md
    assert "Pytest Runtime Profile" in md


def test_milestone_packet_warn_on_migration_warn(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    (p["migration"]).write_text(json.dumps({"status": "warn"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )


def test_milestone_packet_blocks_when_routine_stability_blocked(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    routine_stability = tmp_path / "routine_stability.json"
    routine_stability.write_text(
        json.dumps({"status": "blocked", "review_state": "blocked", "blocking": True}),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        routine_release_cycle_stability_report=routine_stability,
    )
    assert packet["blocking"] is True
    assert "routine_release_cycle_stability_status=blocked" in packet["blocking_reasons"]
    md = render_validation_milestone_packet_markdown(packet)
    assert "Routine Release-Cycle Stability" in md
    assert packet["overall_status"] == "fail"


def test_milestone_packet_includes_post_removal_closure_summary(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    closure = tmp_path / "closure.json"
    closure.write_text(
        json.dumps(
            {
                "status": "closed",
                "canonical_only_manifest_confirmed": True,
                "history_update_absent": True,
                "remaining_followups": [],
            }
        ),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_post_removal_closure=closure,
    )
    assert packet["alias_post_removal_closure_summary"]["status"] == "closed"
    md = render_validation_milestone_packet_markdown(packet)
    assert "Alias Post-Removal Closure" in md


def test_milestone_packet_includes_final_release_ready_closure_summary(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    closure = tmp_path / "release_ready_closure.json"
    closure.write_text(
        json.dumps(
            {
                "status": "ready",
                "recommendation": "ready_for_review",
                "remaining_blockers": [],
            }
        ),
        encoding="utf-8",
    )
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        release_ready_closure=closure,
    )
    assert packet["release_ready_closure_summary"]["status"] == "ready"
    md = render_validation_milestone_packet_markdown(packet)
    assert "Final Release-Ready Closure" in md


def test_milestone_ready_for_review_semantics_when_non_blocking_governance_watch(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    alias_sunset = tmp_path / "alias_sunset.json"
    readiness = tmp_path / "readiness.json"
    closure = tmp_path / "closure.json"
    reviewer_packet = tmp_path / "reviewer.json"
    alias_post = tmp_path / "alias_post.json"
    cadence = tmp_path / "cadence.json"
    checklist = tmp_path / "checklist.json"
    followups = tmp_path / "followups.json"
    governance = tmp_path / "governance.json"
    external_governance = tmp_path / "external_governance.json"
    external_evidence = tmp_path / "external_evidence.json"
    archive_closure = tmp_path / "archive_closure.json"
    handoff_seal = tmp_path / "handoff_seal.json"
    runtime_cycle = tmp_path / "runtime_cycle.json"
    runtime_variance = tmp_path / "runtime_variance.json"
    alias_sunset.write_text(json.dumps({"status": "watch"}), encoding="utf-8")
    readiness.write_text(json.dumps({"status": "ready", "superseded_watch_items": ["alias_sunset_decision_gate=watch"]}), encoding="utf-8")
    closure.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    reviewer_packet.write_text(json.dumps({"status": "ready_for_review"}), encoding="utf-8")
    alias_post.write_text(json.dumps({"status": "closed"}), encoding="utf-8")
    cadence.write_text(json.dumps({"status": "routine", "recommended_cadence": "next_release_cycle"}), encoding="utf-8")
    checklist.write_text(json.dumps({"status": "ready", "mode": "routine_maintenance", "optional_followup_count": 2}), encoding="utf-8")
    followups.write_text(json.dumps({"status": "open", "blocking": False, "items": [{"id": "x"}, {"id": "y"}]}), encoding="utf-8")
    governance.write_text(json.dumps({"status": "watch", "conclusion": "watch_non_blocking"}), encoding="utf-8")
    external_governance.write_text(json.dumps({"status": "tracked", "blocking": False, "release_readiness_impact": "none"}), encoding="utf-8")
    external_evidence.write_text(json.dumps({"status": "closed_unresolved_external", "blocking": False}), encoding="utf-8")
    archive_closure.write_text(json.dumps({"status": "ready", "blocking": False}), encoding="utf-8")
    handoff_seal.write_text(json.dumps({"status": "sealed", "blocking": False}), encoding="utf-8")
    runtime_cycle.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    runtime_variance.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_sunset_review=alias_sunset,
        release_readiness_report=readiness,
        release_ready_closure=closure,
        final_reviewer_packet=reviewer_packet,
        alias_post_removal_closure=alias_post,
        maintenance_cadence=cadence,
        maintenance_checklist=checklist,
        optional_followups=followups,
        maintenance_governance_closure=governance,
        external_consumer_governance=external_governance,
        external_consumer_evidence_closure_report=external_evidence,
        final_maintenance_archive_closure_report=archive_closure,
        post_freeze_handoff_seal_report=handoff_seal,
        runtime_release_cycle_report=runtime_cycle,
        runtime_variance_report=runtime_variance,
    )
    assert packet["overall_status"] == "watch"
    assert packet["review_state"] == "ready_for_review"
    assert packet["blocking"] is False
    assert "alias_sunset_decision_gate=watch" in packet["superseded_watch_items"]
    assert packet["maintenance_cadence"] == "next_release_cycle"
    assert packet["maintenance_checklist_summary"]["status"] == "ready"
    assert packet["optional_followups_summary"]["status"] == "open"
    assert packet["maintenance_governance_closure_summary"]["status"] == "watch"
    assert packet["external_consumer_governance_summary"]["status"] == "tracked"
    assert packet["external_consumer_evidence_closure_summary"]["status"] == "closed_unresolved_external"
    assert packet["final_maintenance_archive_closure_summary"]["status"] == "ready"
    assert packet["post_freeze_handoff_seal_summary"]["status"] == "sealed"


def test_cli_missing_critical_fails_without_warn_only(tmp_path: Path) -> None:
    out_json = tmp_path / "o.json"
    out_md = tmp_path / "o.md"
    code = milestone_main(
        [
            "--review-bundle-root",
            str(tmp_path / "missing-default"),
            "--alias-fallback-bundle-root",
            str(tmp_path / "missing-alias"),
            "--runtime-edge-report",
            str(tmp_path / "missing-edge.json"),
            "--migration-readiness-report",
            str(tmp_path / "missing-migration.json"),
            "--runtime-budget-report",
            str(tmp_path / "missing-budget.json"),
            "--data-source-audit-report",
            str(tmp_path / "missing-audit.json"),
            "--fast-timing-json",
            str(tmp_path / "missing-timing.json"),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ]
    )
    assert code != 0
