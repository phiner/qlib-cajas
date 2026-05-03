import json
from pathlib import Path

from cajas.reports.validation_final_reviewer_packet import (
    build_validation_final_reviewer_packet,
    render_validation_final_reviewer_packet_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path):
    return {
        "release_ready_closure": _write(tmp_path / "rrc.json", {"status": "watch", "ready_for_review": True, "blocking": False, "remaining_followups": ["monitor runtime variance next release cycle"]}),
        "alias_post_removal_closure": _write(tmp_path / "alias.json", {"status": "closed"}),
        "runtime_variance_closure": _write(tmp_path / "rvc.json", {"status": "monitoring_only"}),
        "release_readiness_report": _write(tmp_path / "readiness.json", {"legacy_read_normalization_kept": True}),
        "milestone_packet": _write(tmp_path / "milestone.json", {"overall_status": "watch"}),
        "review_bundle_manifest": _write(tmp_path / "manifest.json", {"history": {"status": "pass"}}),
        "manifest_compatibility_report": _write(tmp_path / "compat.json", {"status": "pass"}),
        "runtime_budget_report": _write(tmp_path / "budget.json", {"overall_status": "pass"}),
        "runtime_edge_report": _write(tmp_path / "edge.json", {"status": "pass"}),
        "data_source_audit_report": _write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}}),
        "maintenance_cadence": _write(
            tmp_path / "cadence.json",
            {
                "status": "routine",
                "recommended_cadence": "next_release_cycle",
                "routine_commands": ["run_fast_validation.py --tier fast"],
                "watch_items": [],
            },
        ),
        "maintenance_checklist": _write(
            tmp_path / "checklist.json",
            {
                "status": "ready",
                "mode": "routine_maintenance",
                "canonical_artifacts": ["tmp/validation-final-reviewer-packet.md"],
            },
        ),
        "optional_followups": _write(
            tmp_path / "followups.json",
            {
                "status": "open",
                "blocking": False,
                "items": [{"id": "slow-test-optimization"}],
            },
        ),
        "maintenance_governance_closure": _write(
            tmp_path / "governance.json",
            {
                "status": "ready",
                "conclusion": "routine",
            },
        ),
        "external_consumer_governance": _write(
            tmp_path / "external_governance.json",
            {
                "status": "routine",
                "blocking": False,
                "release_readiness_impact": "none",
            },
        ),
        "external_consumer_evidence_closure_report": _write(
            tmp_path / "external_evidence_closure.json",
            {"status": "closed_unresolved_external", "blocking": False},
        ),
        "final_maintenance_archive_closure_report": _write(
            tmp_path / "archive_closure.json",
            {"status": "ready", "blocking": False},
        ),
        "post_freeze_handoff_seal_report": _write(
            tmp_path / "handoff_seal.json",
            {"status": "sealed", "blocking": False},
        ),
        "routine_release_cycle_stability_report": _write(
            tmp_path / "routine_stability.json",
            {"status": "stable", "review_state": "ready_for_review", "blocking": False},
        ),
    }


def test_final_reviewer_packet_ready_for_review(tmp_path: Path) -> None:
    i = _inputs(tmp_path)
    packet = build_validation_final_reviewer_packet(**i)
    assert packet["status"] == "ready_for_review"
    assert packet["summary"]["canonical_only_manifest"] is True
    assert packet["maintenance_cadence_status"] == "routine"
    assert packet["maintenance_checklist_status"] == "ready"
    assert packet["optional_followups_count"] == 1
    assert packet["maintenance_governance_closure_status"] == "ready"
    assert packet["external_consumer_governance_status"] == "routine"
    assert packet["final_maintenance_archive_closure_status"] == "ready"
    assert packet["post_freeze_handoff_seal_status"] == "sealed"
    assert packet["routine_release_cycle_stability_status"] == "stable"
    md = render_validation_final_reviewer_packet_markdown(packet)
    assert "Reviewer Handoff" in md
    assert "Governance Closure" in md
    assert "External Consumer Governance" in md
    assert "External Consumer Evidence Closure" in md
    assert "Final Maintenance Archive Closure" in md
    assert "Post-Freeze Handoff Seal" in md
    assert "Routine Release-Cycle Stability" in md
    assert "Optional Followup Queue" in md
    assert "Scope Boundary" in md


def test_final_reviewer_packet_blocked_on_runtime_or_compat_fail(tmp_path: Path) -> None:
    i = _inputs(tmp_path)
    _write(i["manifest_compatibility_report"], {"status": "fail"})
    packet = build_validation_final_reviewer_packet(**i)
    assert packet["status"] == "blocked"
