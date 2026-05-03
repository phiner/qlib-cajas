import json
from pathlib import Path

from cajas.reports.validation_alias_removal_plan import (
    build_alias_removal_plan,
    render_alias_removal_plan_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_alias_removal_plan_not_ready_when_sunset_watch(tmp_path: Path) -> None:
    sunset = _write(
        tmp_path / "sunset.json",
        {
            "status": "watch",
            "requires_alias_count": 0,
            "decision_gate": {"required_evidence_complete": False},
        },
    )
    migration = _write(tmp_path / "migration.json", {"status": "pass"})
    report = build_alias_removal_plan(alias_sunset_review=sunset, migration_readiness_report=migration)
    assert report["status"] == "not_ready"
    assert report["recommendation"] == "keep_fallback"


def test_alias_removal_plan_ready_to_schedule_when_sunset_ready(tmp_path: Path) -> None:
    sunset = _write(
        tmp_path / "sunset.json",
        {
            "status": "ready",
            "requires_alias_count": 0,
            "decision_gate": {"required_evidence_complete": True},
        },
    )
    migration = _write(tmp_path / "migration.json", {"status": "pass"})
    report = build_alias_removal_plan(alias_sunset_review=sunset, migration_readiness_report=migration)
    assert report["status"] == "ready_to_schedule"
    assert report["recommendation"] == "schedule_removal_phase"


def test_alias_removal_plan_blocked_when_sunset_blocked(tmp_path: Path) -> None:
    sunset = _write(
        tmp_path / "sunset.json",
        {
            "status": "blocked",
            "requires_alias_count": 1,
            "decision_gate": {"required_evidence_complete": False},
        },
    )
    migration = _write(tmp_path / "migration.json", {"status": "pass"})
    report = build_alias_removal_plan(alias_sunset_review=sunset, migration_readiness_report=migration)
    assert report["status"] == "blocked"
    md = render_alias_removal_plan_markdown(report)
    assert "does not remove alias fallback" in md
