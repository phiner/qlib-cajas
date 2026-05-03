import json
from pathlib import Path

from cajas.reports.validation_evidence_candidate_approval import (
    build_evidence_candidate_approval_report,
    render_evidence_candidate_approval_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    real = _write(tmp_path / "real.json", {"consumers": [{"name": "external_unknown_consumer", "status": "unknown"}]})
    candidate = _write(
        tmp_path / "candidate.json",
        {"consumers": [{"name": "external_unknown_consumer", "status": "confirmed_clear"}]},
    )
    owner_validation = _write(
        tmp_path / "owner_validation.json",
        {"status": "valid_ready_to_apply", "safe_to_update_evidence": True},
    )
    candidate_report = _write(tmp_path / "candidate_report.json", {"status": "ready_candidate"})
    sunset = _write(tmp_path / "sunset.json", {"status": "ready"})
    removal = _write(tmp_path / "removal.json", {"status": "ready_to_schedule"})
    return {
        "real": real,
        "candidate": candidate,
        "owner_validation": owner_validation,
        "candidate_report": candidate_report,
        "sunset": sunset,
        "removal": removal,
    }


def test_approval_required_without_approval_file(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    report = build_evidence_candidate_approval_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        owner_response_validation=p["owner_validation"],
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_review=p["sunset"],
        alias_removal_plan=p["removal"],
    )
    assert report["status"] == "approval_required"
    assert report["candidate_valid"] is True
    assert report["candidate_safe_to_apply"] is True


def test_approval_required_when_approved_false(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    approval = _write(tmp_path / "approval.json", {"approved": False, "approver": "reviewer"})
    report = build_evidence_candidate_approval_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        owner_response_validation=p["owner_validation"],
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_review=p["sunset"],
        alias_removal_plan=p["removal"],
        approval_file=approval,
    )
    assert report["status"] == "approval_required"


def test_approved_candidate_when_approved_true(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    approval = _write(tmp_path / "approval.json", {"approved": True, "approver": "reviewer"})
    report = build_evidence_candidate_approval_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        owner_response_validation=p["owner_validation"],
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_review=p["sunset"],
        alias_removal_plan=p["removal"],
        approval_file=approval,
    )
    assert report["status"] == "approved_candidate"
    md = render_evidence_candidate_approval_markdown(report)
    assert "Do not remove fallback in this phase." in md


def test_invalid_when_candidate_invalid(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    owner_validation = _write(
        tmp_path / "owner_validation_bad.json",
        {"status": "invalid", "safe_to_update_evidence": False},
    )
    report = build_evidence_candidate_approval_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        owner_response_validation=owner_validation,
        consumer_evidence_candidate_report=p["candidate_report"],
        alias_sunset_review=p["sunset"],
        alias_removal_plan=p["removal"],
    )
    assert report["status"] == "invalid"
