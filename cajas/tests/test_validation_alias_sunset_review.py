import json
from pathlib import Path

from cajas.reports.validation_alias_sunset_review import build_alias_sunset_review


def _write_inputs(tmp_path: Path, migration_status: str = "pass", milestone_status: str = "pass") -> tuple[Path, Path]:
    migration = {
        "status": migration_status,
        "alias_fallback": {
            "default_emits_alias": False,
            "fallback_flag": "--include-history-update-alias",
            "fallback_manifest_has_alias": True,
        },
    }
    milestone = {"overall_status": milestone_status}
    migration_path = tmp_path / "migration.json"
    milestone_path = tmp_path / "milestone.json"
    migration_path.write_text(json.dumps(migration), encoding="utf-8")
    milestone_path.write_text(json.dumps(milestone), encoding="utf-8")
    return migration_path, milestone_path


def test_alias_sunset_unknown_is_watch(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="unknown",
    )
    assert report["status"] == "watch"
    assert report["recommended_action"] == "collect_consumer_evidence"
    assert report["evidence_complete"] is False


def test_alias_sunset_requires_alias_is_blocked(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="requires_alias",
    )
    assert report["status"] == "blocked"
    assert report["recommended_action"] == "migrate_consumers"


def test_alias_sunset_confirmed_clear_is_ready(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="confirmed_clear",
    )
    assert report["status"] == "ready"
    assert report["recommended_action"] == "schedule_removal"
    assert report["decision_gate"]["status"] == "ready"
    assert report["decision_gate"]["required_evidence_complete"] is False
    assert report["evidence_completeness_ratio"] == 0.0


def test_alias_sunset_uses_evidence_when_cli_status_missing(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "external_status": "requires_alias",
                "consumers": [{"name": "ext", "requires_history_update": True, "status": "requires_alias"}],
            }
        ),
        encoding="utf-8",
    )
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        consumer_evidence=evidence,
    )
    assert report["status"] == "blocked"


def test_alias_sunset_cli_status_overrides_evidence(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "external_status": "unknown",
                "consumers": [{"name": "ext", "requires_history_update": False, "status": "unknown"}],
            }
        ),
        encoding="utf-8",
    )
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="confirmed_clear",
        consumer_evidence=evidence,
    )
    # Because one unresolved consumer remains, this remains watch despite confirmed_clear override.
    assert report["status"] == "watch"
    assert report["recommended_action"] == "collect_consumer_evidence"
    assert report["decision_gate"]["status"] == "watch"


def test_alias_sunset_blocked_when_consumer_requires_alias_in_evidence(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "external_status": "unknown",
                "consumers": [
                    {
                        "name": "legacy-consumer",
                        "owner": "external-team",
                        "status": "requires_alias",
                        "requires_history_update": True,
                        "evidence": "still reading history_update",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        consumer_evidence=evidence,
    )
    assert report["status"] == "blocked"
    assert report["decision_gate"]["status"] == "blocked"
    assert report["decision_gate"]["consumers_requiring_alias"][0]["name"] == "legacy-consumer"
