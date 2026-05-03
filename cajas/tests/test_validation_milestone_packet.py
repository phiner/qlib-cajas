import json
from pathlib import Path

from cajas.reports.validation_milestone_packet import (
    build_validation_milestone_packet,
    render_validation_milestone_packet_markdown,
)
from cajas.scripts.build_validation_milestone_packet import main as milestone_main


def _write_bundle(root: Path, *, overall: str = "pass") -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "final_status.json").write_text(json.dumps({"overall_status": overall}), encoding="utf-8")
    (root / "profile_matrix.json").write_text(
        json.dumps({"profiles": {"local": {"overall_status": "pass"}, "ci": {"overall_status": "pass"}, "strict": {"overall_status": "warn"}}}),
        encoding="utf-8",
    )
    (root / "review_bundle_index.md").write_text("# idx", encoding="utf-8")
    (root / "final_status.md").write_text("# final", encoding="utf-8")
    (root / "review_bundle_manifest.json").write_text(json.dumps({"manifest_compatibility": {"status": "pass"}}), encoding="utf-8")
    (root / "delivery_packet").mkdir(parents=True, exist_ok=True)
    (root / "delivery_packet" / "packet_manifest.json").write_text(json.dumps({"overall_status": "pass"}), encoding="utf-8")


def _write_common_inputs(tmp_path: Path) -> dict[str, Path]:
    default = tmp_path / "default"
    alias = tmp_path / "alias-fallback"
    _write_bundle(default, overall="pass")
    _write_bundle(alias, overall="pass")
    (tmp_path / "runtime-edge.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (tmp_path / "migration.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (tmp_path / "runtime-budget.json").write_text(
        json.dumps({"overall_status": "pass", "timing_consistency": {"status": "pass"}, "results": []}),
        encoding="utf-8",
    )
    (tmp_path / "audit.json").write_text(json.dumps({"summary": {"read_csv_count": 29}}), encoding="utf-8")
    (tmp_path / "timing.json").write_text(json.dumps({"total_seconds": 84.0}), encoding="utf-8")
    return {
        "default": default,
        "alias": alias,
        "runtime_edge": tmp_path / "runtime-edge.json",
        "migration": tmp_path / "migration.json",
        "runtime_budget": tmp_path / "runtime-budget.json",
        "audit": tmp_path / "audit.json",
        "timing": tmp_path / "timing.json",
    }


def test_milestone_packet_build_pass(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )
    assert packet["overall_status"] == "pass"
    assert "artifact_map" in packet
    md = render_validation_milestone_packet_markdown(packet)
    assert "Scope Boundary" in md
    assert "Primary Reviewer Artifacts" in md


def test_milestone_packet_watch_status(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    (p["runtime_edge"]).write_text(json.dumps({"status": "watch"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )
    assert packet["overall_status"] == "watch"


def test_milestone_packet_includes_optional_alias_and_runtime_cycle(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    alias_sunset = tmp_path / "alias_sunset.json"
    runtime_cycle = tmp_path / "runtime_cycle.json"
    alias_sunset.write_text(json.dumps({"status": "watch", "recommended_action": "keep_fallback"}), encoding="utf-8")
    runtime_cycle.write_text(json.dumps({"status": "watch", "next_review_trigger": "remaining_budget_ratio_below_0.15"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_sunset_review=alias_sunset,
        runtime_release_cycle_report=runtime_cycle,
    )
    assert packet["alias_sunset_review_summary"]["status"] == "watch"
    assert packet["runtime_release_cycle_summary"]["status"] == "watch"


def test_milestone_packet_includes_runtime_variance_and_watch_reason(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    alias_sunset = tmp_path / "alias_sunset.json"
    runtime_cycle = tmp_path / "runtime_cycle.json"
    runtime_variance = tmp_path / "runtime_variance.json"
    alias_sunset.write_text(json.dumps({"status": "watch", "recommended_action": "keep_fallback"}), encoding="utf-8")
    runtime_cycle.write_text(json.dumps({"status": "pass", "next_review_trigger": "manual_next_release"}), encoding="utf-8")
    runtime_variance.write_text(json.dumps({"status": "watch", "recommendation": "watch_next_cycle"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
        alias_sunset_review=alias_sunset,
        runtime_release_cycle_report=runtime_cycle,
        runtime_variance_report=runtime_variance,
    )
    assert packet["runtime_variance_summary"]["status"] == "watch"
    assert packet["overall_status"] == "watch"


def test_milestone_packet_warn_on_migration_warn(tmp_path: Path) -> None:
    p = _write_common_inputs(tmp_path)
    (p["migration"]).write_text(json.dumps({"status": "warn"}), encoding="utf-8")
    packet = build_validation_milestone_packet(
        review_bundle_root=p["default"],
        alias_fallback_bundle_root=p["alias"],
        runtime_edge_report=p["runtime_edge"],
        migration_readiness_report=p["migration"],
        runtime_budget_report=p["runtime_budget"],
        data_source_audit_report=p["audit"],
        fast_timing_json=p["timing"],
    )
    assert packet["overall_status"] == "warn"


def test_cli_missing_critical_fails_without_warn_only(tmp_path: Path) -> None:
    out_json = tmp_path / "o.json"
    out_md = tmp_path / "o.md"
    code = milestone_main(
        [
            "--review-bundle-root",
            str(tmp_path / "missing-default"),
            "--alias-fallback-bundle-root",
            str(tmp_path / "missing-alias"),
            "--runtime-edge-report",
            str(tmp_path / "missing-edge.json"),
            "--migration-readiness-report",
            str(tmp_path / "missing-migration.json"),
            "--runtime-budget-report",
            str(tmp_path / "missing-budget.json"),
            "--data-source-audit-report",
            str(tmp_path / "missing-audit.json"),
            "--fast-timing-json",
            str(tmp_path / "missing-timing.json"),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ]
    )
    assert code != 0
