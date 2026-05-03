import json
from pathlib import Path

from cajas.reports.validation_alias_post_removal_closure import (
    build_validation_alias_post_removal_closure,
    render_validation_alias_post_removal_closure_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_post_removal_closure_closed(tmp_path: Path) -> None:
    manifest = _write(tmp_path / "manifest.json", {"history": {"status": "pass"}})
    compat = _write(tmp_path / "compat.json", {"status": "pass"})
    fallback = _write(
        tmp_path / "fallback.json",
        {"legacy_read_normalization_kept": True, "rollback_plan": ["revert"]},
    )
    budget = _write(tmp_path / "budget.json", {"overall_status": "pass", "timing_consistency": {"status": "pass"}})
    edge = _write(tmp_path / "edge.json", {"status": "pass"})
    audit = _write(tmp_path / "audit.json", {"summary": {"read_csv_count": 29}})
    report = build_validation_alias_post_removal_closure(
        review_bundle_manifest=manifest,
        manifest_compatibility_report=compat,
        alias_fallback_removal_readiness=fallback,
        runtime_budget_report=budget,
        runtime_edge_report=edge,
        data_source_audit_report=audit,
    )
    assert report["status"] == "closed"
    assert report["canonical_only_manifest_confirmed"] is True
    assert report["history_update_absent"] is True
    assert report["release_readiness_status"] == "ready"
    md = render_validation_alias_post_removal_closure_markdown(report)
    assert "Scope Boundary" in md


def test_post_removal_closure_blocked_on_runtime_or_compat_fail(tmp_path: Path) -> None:
    manifest = _write(tmp_path / "manifest.json", {"history": {"status": "pass"}, "history_update": {"deprecated": True}})
    compat = _write(tmp_path / "compat.json", {"status": "fail"})
    fallback = _write(tmp_path / "fallback.json", {"legacy_read_normalization_kept": False, "rollback_plan": []})
    budget = _write(tmp_path / "budget.json", {"overall_status": "fail", "timing_consistency": {"status": "fail"}})
    edge = _write(tmp_path / "edge.json", {"status": "fail"})
    audit = _write(tmp_path / "audit.json", {"summary": {}})
    report = build_validation_alias_post_removal_closure(
        review_bundle_manifest=manifest,
        manifest_compatibility_report=compat,
        alias_fallback_removal_readiness=fallback,
        runtime_budget_report=budget,
        runtime_edge_report=edge,
        data_source_audit_report=audit,
    )
    assert report["status"] == "blocked"
    assert "manifest_compatibility_fail" in report["blocking_items"]
    assert "runtime_budget_fail" in report["blocking_items"]
