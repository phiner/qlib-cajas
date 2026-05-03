import json
from pathlib import Path

from cajas.reports.validation_canonical_evidence_update_plan import (
    build_canonical_evidence_update_plan,
    render_canonical_evidence_update_plan_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    real = _write(
        tmp_path / "real.json",
        {"consumers": [{"name": "external_unknown_consumer", "status": "unknown"}]},
    )
    candidate = _write(
        tmp_path / "candidate.json",
        {"consumers": [{"name": "external_unknown_consumer", "status": "confirmed_clear"}]},
    )
    owner = _write(tmp_path / "owner.json", {"status": "valid_ready_to_apply"})
    candidate_report = _write(tmp_path / "candidate_report.json", {"status": "ready_candidate"})
    return {
        "real": real,
        "candidate": candidate,
        "owner": owner,
        "candidate_report": candidate_report,
    }


def test_update_plan_not_ready_without_approval(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    approval = _write(tmp_path / "approval.json", {"status": "approval_required"})
    schedule = _write(tmp_path / "schedule.json", {"status": "not_scheduled"})
    plan = build_canonical_evidence_update_plan(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        evidence_candidate_approval_report=approval,
        owner_response_validation=p["owner"],
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_schedule=schedule,
    )
    assert plan["status"] == "not_ready"


def test_update_plan_ready_to_apply_when_approved_and_schedule_ready(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    approval = _write(tmp_path / "approval.json", {"status": "approved_candidate"})
    schedule = _write(tmp_path / "schedule.json", {"status": "ready_to_schedule"})
    plan = build_canonical_evidence_update_plan(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        evidence_candidate_approval_report=approval,
        owner_response_validation=p["owner"],
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_schedule=schedule,
    )
    assert plan["status"] == "ready_to_apply"
    assert plan["recommendation"] == "apply_in_dedicated_phase"
    assert plan["evidence_diff_summary"]["status_changes"][0]["from"] == "unknown"
    assert plan["evidence_diff_summary"]["status_changes"][0]["to"] == "confirmed_clear"
    md = render_canonical_evidence_update_plan_markdown(plan)
    assert "do_not_auto_apply" in md


def test_update_plan_blocked_when_candidate_invalid(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    bad_owner = _write(tmp_path / "owner_bad.json", {"status": "invalid_ready_to_apply"})
    approval = _write(tmp_path / "approval.json", {"status": "approved_candidate"})
    schedule = _write(tmp_path / "schedule.json", {"status": "ready_to_schedule"})
    plan = build_canonical_evidence_update_plan(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        evidence_candidate_approval_report=approval,
        owner_response_validation=bad_owner,
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_schedule=schedule,
    )
    assert plan["status"] == "blocked"
