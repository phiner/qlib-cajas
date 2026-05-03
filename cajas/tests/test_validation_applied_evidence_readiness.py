import json
from pathlib import Path

from cajas.reports.validation_applied_evidence_readiness import (
    build_applied_evidence_readiness_report,
    render_applied_evidence_readiness_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_applied_readiness_ready_for_real_apply(tmp_path: Path) -> None:
    real_readiness = _write(tmp_path / "real_readiness.json", {"status": "watch"})
    real_sunset = _write(tmp_path / "real_sunset.json", {"status": "watch"})
    applied_closure = _write(tmp_path / "applied_closure.json", {"status": "complete"})
    applied_sunset = _write(tmp_path / "applied_sunset.json", {"status": "ready"})
    applied_removal = _write(tmp_path / "applied_removal.json", {"status": "ready_to_schedule"})
    apply_report = _write(tmp_path / "apply_report.json", {"status": "dry_run_ready"})
    budget = _write(tmp_path / "budget.json", {"overall_status": "pass"})
    edge = _write(tmp_path / "edge.json", {"status": "pass"})
    report = build_applied_evidence_readiness_report(
        real_release_readiness=real_readiness,
        real_alias_sunset=real_sunset,
        applied_evidence_closure=applied_closure,
        applied_alias_sunset=applied_sunset,
        applied_alias_removal_plan=applied_removal,
        applied_canonical_evidence_apply_report=apply_report,
        runtime_budget_report=budget,
        runtime_edge_report=edge,
    )
    assert report["status"] == "ready_for_real_apply"
    assert report["alias_fallback_removal_ready_after_real_apply"] is True
    md = render_applied_evidence_readiness_markdown(report)
    assert "do_not_remove_fallback_in_this_phase" in md


def test_applied_readiness_watch_when_projection_not_ready(tmp_path: Path) -> None:
    real_readiness = _write(tmp_path / "real_readiness.json", {"status": "watch"})
    real_sunset = _write(tmp_path / "real_sunset.json", {"status": "watch"})
    applied_closure = _write(tmp_path / "applied_closure.json", {"status": "incomplete"})
    applied_sunset = _write(tmp_path / "applied_sunset.json", {"status": "watch"})
    applied_removal = _write(tmp_path / "applied_removal.json", {"status": "not_ready"})
    apply_report = _write(tmp_path / "apply_report.json", {"status": "dry_run_ready"})
    budget = _write(tmp_path / "budget.json", {"overall_status": "pass"})
    edge = _write(tmp_path / "edge.json", {"status": "pass"})
    report = build_applied_evidence_readiness_report(
        real_release_readiness=real_readiness,
        real_alias_sunset=real_sunset,
        applied_evidence_closure=applied_closure,
        applied_alias_sunset=applied_sunset,
        applied_alias_removal_plan=applied_removal,
        applied_canonical_evidence_apply_report=apply_report,
        runtime_budget_report=budget,
        runtime_edge_report=edge,
    )
    assert report["status"] == "watch"
