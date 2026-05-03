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
