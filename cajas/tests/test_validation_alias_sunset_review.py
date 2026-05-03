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
    assert report["recommended_action"] == "keep_fallback"


def test_alias_sunset_requires_alias_is_blocked(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="requires_alias",
    )
    assert report["status"] == "blocked"
    assert report["recommended_action"] == "keep_fallback"


def test_alias_sunset_confirmed_clear_is_ready(tmp_path: Path) -> None:
    migration, milestone = _write_inputs(tmp_path)
    report = build_alias_sunset_review(
        migration_readiness_report=migration,
        milestone_packet=milestone,
        external_consumer_status="confirmed_clear",
    )
    assert report["status"] == "ready"
    assert report["recommended_action"] == "schedule_removal"
