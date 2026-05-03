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
                {"name": "b", "owner": "external-review-needed", "status": "unknown", "evidence": "", "next_action": "identify_owner", "blocking_alias_sunset": True},
            ]
        },
    )
    report = build_consumer_evidence_closure_report(consumer_evidence=evidence)
    assert report["status"] == "incomplete"
    assert report["unresolved_count"] == 1
    assert report["blocking_consumer_count"] == 1
    assert report["owner_missing_count"] == 1
    assert report["action_plan"][0]["next_action"] == "identify_owner"


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


def test_consumer_evidence_promotion_path_complete_when_all_fields_set(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {
            "consumers": [
                {
                    "name": "external",
                    "owner": "external-team",
                    "status": "confirmed_clear",
                    "evidence": "validated",
                    "last_checked": "2026-05-03",
                    "next_action": "none",
                    "blocking_alias_sunset": False,
                }
            ]
        },
    )
    report = build_consumer_evidence_closure_report(consumer_evidence=evidence)
    assert report["status"] == "complete"


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
