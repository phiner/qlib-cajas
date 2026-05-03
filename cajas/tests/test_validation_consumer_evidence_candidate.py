import json
from pathlib import Path

from cajas.reports.validation_consumer_evidence_candidate import (
    build_consumer_evidence_candidate_report,
    render_consumer_evidence_candidate_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_candidate_report_ready_candidate(tmp_path: Path) -> None:
    candidate = _write(tmp_path / "candidate.json", {"consumers": [{"name": "external_unknown_consumer"}]})
    closure = _write(tmp_path / "closure.json", {"status": "complete"})
    sunset = _write(tmp_path / "sunset.json", {"status": "ready"})
    removal = _write(tmp_path / "removal.json", {"status": "ready_to_schedule"})
    payload = build_consumer_evidence_candidate_report(
        candidate_evidence=candidate,
        consumer_evidence_closure_report=closure,
        alias_sunset_review=sunset,
        alias_removal_plan=removal,
    )
    assert payload["status"] == "ready_candidate"
    assert payload["release_readiness_projected_status"] == "ready"
    md = render_consumer_evidence_candidate_markdown(payload)
    assert "manual_approval_required" in md
    assert "do_not_auto_apply" in md


def test_candidate_report_blocked_when_incomplete(tmp_path: Path) -> None:
    candidate = _write(tmp_path / "candidate.json", {"consumers": [{"name": "external_unknown_consumer"}]})
    closure = _write(tmp_path / "closure.json", {"status": "incomplete"})
    sunset = _write(tmp_path / "sunset.json", {"status": "watch"})
    removal = _write(tmp_path / "removal.json", {"status": "not_ready"})
    payload = build_consumer_evidence_candidate_report(
        candidate_evidence=candidate,
        consumer_evidence_closure_report=closure,
        alias_sunset_review=sunset,
        alias_removal_plan=removal,
    )
    assert payload["status"] == "blocked"
    assert payload["release_readiness_projected_status"] == "watch"
