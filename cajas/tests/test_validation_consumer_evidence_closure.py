import json
from pathlib import Path

from cajas.reports.validation_consumer_evidence_closure import build_consumer_evidence_closure_report


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_consumer_evidence_closure_incomplete_for_unresolved(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {
            "consumers": [
                {"name": "a", "owner": "team", "status": "confirmed_clear", "evidence": "ok", "next_action": "none"},
                {"name": "b", "owner": "external", "status": "unknown", "evidence": "", "next_action": "identify_owner"},
            ]
        },
    )
    report = build_consumer_evidence_closure_report(consumer_evidence=evidence)
    assert report["status"] == "incomplete"
    assert report["unresolved_count"] == 1


def test_consumer_evidence_closure_complete_for_confirmed_clear(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {
            "consumers": [
                {"name": "a", "owner": "team", "status": "confirmed_clear", "evidence": "ok", "next_action": "none"},
                {"name": "b", "owner": "external", "status": "confirmed_clear", "evidence": "ok", "next_action": "none"},
            ]
        },
    )
    report = build_consumer_evidence_closure_report(consumer_evidence=evidence)
    assert report["status"] == "complete"
    assert report["evidence_complete"] is True


def test_consumer_evidence_closure_blocked_for_requires_alias(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {
            "consumers": [
                {"name": "legacy", "owner": "team", "status": "requires_alias", "evidence": "legacy path", "next_action": "migrate_consumer"}
            ]
        },
    )
    report = build_consumer_evidence_closure_report(consumer_evidence=evidence)
    assert report["status"] == "blocked"
