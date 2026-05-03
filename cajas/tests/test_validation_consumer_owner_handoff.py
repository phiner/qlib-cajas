import json
from pathlib import Path

from cajas.reports.validation_consumer_owner_handoff import (
    build_consumer_owner_handoff,
    render_consumer_owner_handoff_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_owner_handoff_open_for_unresolved_consumer(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {"consumers": [{"name": "x", "owner": "external-review-needed", "status": "unknown", "next_action": "identify_owner"}]},
    )
    report = build_consumer_owner_handoff(consumer_evidence=evidence)
    assert report["status"] == "open"
    assert report["blocking_consumer_count"] == 1
    assert report["handoff_items"][0]["next_action"] == "identify_owner"
    md = render_consumer_owner_handoff_markdown(report)
    assert "Copyable Owner Message" in md


def test_owner_handoff_ready_when_all_confirmed_clear(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {"consumers": [{"name": "x", "owner": "team", "status": "confirmed_clear", "next_action": "none"}]},
    )
    report = build_consumer_owner_handoff(consumer_evidence=evidence)
    assert report["status"] == "ready"
    assert report["handoff_items"] == []


def test_owner_handoff_blocked_when_requires_alias(tmp_path: Path) -> None:
    evidence = _write(
        tmp_path / "evidence.json",
        {"consumers": [{"name": "legacy", "owner": "team", "status": "requires_alias", "next_action": "migrate_consumer"}]},
    )
    report = build_consumer_owner_handoff(consumer_evidence=evidence)
    assert report["status"] == "blocked"
    assert report["handoff_items"][0]["requires_alias"] is True
