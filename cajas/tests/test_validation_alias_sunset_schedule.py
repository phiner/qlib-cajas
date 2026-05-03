import json
from pathlib import Path

from cajas.reports.validation_alias_sunset_schedule import (
    build_alias_sunset_schedule,
    render_alias_sunset_schedule_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _common(tmp_path: Path) -> dict[str, Path]:
    removal = _write(tmp_path / "removal.json", {"status": "ready_to_schedule"})
    release = _write(tmp_path / "release.json", {"status": "watch"})
    milestone = _write(tmp_path / "milestone.json", {"overall_status": "watch"})
    return {"removal": removal, "release": release, "milestone": milestone}


def test_schedule_not_scheduled_when_approval_required(tmp_path: Path) -> None:
    c = _common(tmp_path)
    approval = _write(tmp_path / "approval.json", {"status": "approval_required"})
    packet = build_alias_sunset_schedule(
        evidence_candidate_approval_report=approval,
        alias_removal_plan=c["removal"],
        release_readiness_report=c["release"],
        milestone_packet=c["milestone"],
    )
    assert packet["status"] == "not_scheduled"


def test_schedule_ready_to_schedule_when_approved_and_ready(tmp_path: Path) -> None:
    c = _common(tmp_path)
    approval = _write(tmp_path / "approval.json", {"status": "approved_candidate"})
    packet = build_alias_sunset_schedule(
        evidence_candidate_approval_report=approval,
        alias_removal_plan=c["removal"],
        release_readiness_report=c["release"],
        milestone_packet=c["milestone"],
    )
    assert packet["status"] == "ready_to_schedule"
    md = render_alias_sunset_schedule_markdown(packet)
    assert "Do not remove fallback in this phase." in md


def test_schedule_blocked_when_invalid_approval(tmp_path: Path) -> None:
    c = _common(tmp_path)
    approval = _write(tmp_path / "approval.json", {"status": "invalid"})
    packet = build_alias_sunset_schedule(
        evidence_candidate_approval_report=approval,
        alias_removal_plan=c["removal"],
        release_readiness_report=c["release"],
        milestone_packet=c["milestone"],
    )
    assert packet["status"] == "blocked"
