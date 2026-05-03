import json
from pathlib import Path

from cajas.reports.validation_eurusd_research_readiness import (
    build_validation_eurusd_research_readiness,
    render_validation_eurusd_research_readiness_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_readiness_ready_for_pattern_research(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    assert payload["status"] == "ready_for_pattern_research"


def test_readiness_watch_for_non_blocking_audit_watch(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "watch"}),
    )
    assert payload["status"] == "watch"


def test_readiness_with_clean_view_when_raw_blocked(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean_view.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["raw_dataset_blocked"] is True
    assert payload["clean_view_approved_for_pattern_research"] is True


def test_readiness_blocked_for_blocking_inputs(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "watch"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "blocked"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
    )
    assert payload["status"] == "blocked"


def test_readiness_markdown_policy(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    md = render_validation_eurusd_research_readiness_markdown(payload).lower()
    assert "no live trading" in md
    assert "no qlib core changes" in md


def test_readiness_includes_pattern_candidate_pack_when_provided(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
        pattern_candidate_pack_report=_write(
            tmp_path / "pack.json",
            {"status": "watch", "candidate_count": 321},
        ),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["pattern_candidate_pack_status"] == "watch"
    assert payload["pattern_candidate_count"] == 321
    assert payload["next_action"] == "review_pattern_samples"
