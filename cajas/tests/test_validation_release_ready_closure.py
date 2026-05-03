import json
from pathlib import Path

from cajas.reports.validation_release_ready_closure import build_validation_release_ready_closure


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path):
    alias = _write(tmp_path / "alias.json", {"status": "closed"})
    readiness = _write(tmp_path / "readiness.json", {"status": "ready", "legacy_read_normalization_kept": True})
    milestone = _write(tmp_path / "milestone.json", {"overall_status": "ready"})
    runtime_cycle = _write(tmp_path / "runtime_cycle.json", {"status": "pass"})
    budget = _write(tmp_path / "budget.json", {"overall_status": "pass"})
    edge = _write(tmp_path / "edge.json", {"status": "pass"})
    compat = _write(tmp_path / "compat.json", {"status": "pass"})
    audit = _write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}})
    manifest = _write(tmp_path / "manifest.json", {"history": {"status": "pass"}})
    return alias, readiness, milestone, runtime_cycle, budget, edge, compat, audit, manifest


def test_release_ready_closure_ready(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    report = build_validation_release_ready_closure(
        alias_post_removal_closure=args[0],
        release_readiness_report=args[1],
        milestone_packet=args[2],
        runtime_release_cycle_report=args[3],
        runtime_budget_report=args[4],
        runtime_edge_report=args[5],
        manifest_compatibility_report=args[6],
        data_source_audit_report=args[7],
        review_bundle_manifest=args[8],
    )
    assert report["status"] == "ready"


def test_release_ready_closure_watch(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    _write(args[3], {"status": "watch"})
    report = build_validation_release_ready_closure(
        alias_post_removal_closure=args[0],
        release_readiness_report=args[1],
        milestone_packet=args[2],
        runtime_release_cycle_report=args[3],
        runtime_budget_report=args[4],
        runtime_edge_report=args[5],
        manifest_compatibility_report=args[6],
        data_source_audit_report=args[7],
        review_bundle_manifest=args[8],
    )
    assert report["status"] == "watch"


def test_release_ready_closure_blocked(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    _write(args[6], {"status": "fail"})
    report = build_validation_release_ready_closure(
        alias_post_removal_closure=args[0],
        release_readiness_report=args[1],
        milestone_packet=args[2],
        runtime_release_cycle_report=args[3],
        runtime_budget_report=args[4],
        runtime_edge_report=args[5],
        manifest_compatibility_report=args[6],
        data_source_audit_report=args[7],
        review_bundle_manifest=args[8],
    )
    assert report["status"] == "blocked"
    assert "manifest_compatibility_status=fail" in report["remaining_blockers"]
