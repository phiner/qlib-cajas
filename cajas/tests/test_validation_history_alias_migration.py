import json
from pathlib import Path

from cajas.reports.validation_history_alias_migration import (
    build_history_alias_migration_report,
    render_history_alias_migration_markdown,
)


def _write_bundle(root: Path, *, manifest_compat: str, profiles: dict[str, str], gates: list[dict]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "review_bundle_manifest.json").write_text(
        json.dumps({"manifest_compatibility": {"status": manifest_compat}}),
        encoding="utf-8",
    )
    (root / "profile_matrix.json").write_text(
        json.dumps({"profiles": {k: {"overall_status": v} for k, v in profiles.items()}}),
        encoding="utf-8",
    )
    (root / "final_status.json").write_text(json.dumps({"gates": gates}), encoding="utf-8")


def test_history_alias_migration_pass(tmp_path: Path) -> None:
    gates = [
        {"name": "runtime_budget", "required": True, "status": "pass"},
        {"name": "optional_x", "required": False, "status": "not_run"},
    ]
    profiles = {"local": "pass", "ci": "pass", "strict": "warn"}
    _write_bundle(tmp_path / "default", manifest_compat="pass", profiles=profiles, gates=gates)
    _write_bundle(tmp_path / "no_alias", manifest_compat="pass", profiles=profiles, gates=gates)

    report = build_history_alias_migration_report(
        default_bundle_root=tmp_path / "default",
        no_alias_bundle_root=tmp_path / "no_alias",
    )
    assert report["status"] == "pass"
    assert report["recommendation"] == "ready_for_default_no_alias_trial"
    assert report["comparison_mode"] == "no-alias"
    md = render_history_alias_migration_markdown(report)
    assert "Scope Note" in md


def test_history_alias_migration_fail_on_required_mismatch(tmp_path: Path) -> None:
    _write_bundle(
        tmp_path / "default",
        manifest_compat="pass",
        profiles={"local": "pass", "ci": "pass", "strict": "warn"},
        gates=[{"name": "runtime_budget", "required": True, "status": "pass"}],
    )
    _write_bundle(
        tmp_path / "no_alias",
        manifest_compat="pass",
        profiles={"local": "pass", "ci": "pass", "strict": "warn"},
        gates=[{"name": "runtime_budget", "required": True, "status": "warn"}],
    )
    report = build_history_alias_migration_report(
        default_bundle_root=tmp_path / "default",
        no_alias_bundle_root=tmp_path / "no_alias",
    )
    assert report["status"] == "fail"
    assert report["recommendation"] == "not_ready"


def test_history_alias_migration_warn_on_optional_diff(tmp_path: Path) -> None:
    profiles = {"local": "pass", "ci": "pass", "strict": "warn"}
    _write_bundle(
        tmp_path / "default",
        manifest_compat="pass",
        profiles=profiles,
        gates=[
            {"name": "runtime_budget", "required": True, "status": "pass"},
            {"name": "optional_x", "required": False, "status": "not_run"},
        ],
    )
    _write_bundle(
        tmp_path / "no_alias",
        manifest_compat="pass",
        profiles=profiles,
        gates=[
            {"name": "runtime_budget", "required": True, "status": "pass"},
            {"name": "optional_x", "required": False, "status": "pass"},
        ],
    )
    report = build_history_alias_migration_report(
        default_bundle_root=tmp_path / "default",
        no_alias_bundle_root=tmp_path / "no_alias",
    )
    assert report["status"] == "warn"
    assert report["recommendation"] == "not_ready"


def test_history_alias_migration_alias_fallback_mode(tmp_path: Path) -> None:
    gates = [{"name": "runtime_budget", "required": True, "status": "pass"}]
    profiles = {"local": "pass", "ci": "pass", "strict": "warn"}
    _write_bundle(tmp_path / "default", manifest_compat="pass", profiles=profiles, gates=gates)
    _write_bundle(tmp_path / "alias-fallback", manifest_compat="pass", profiles=profiles, gates=gates)
    report = build_history_alias_migration_report(
        default_bundle_root=tmp_path / "default",
        no_alias_bundle_root=tmp_path / "alias-fallback",
    )
    assert report["comparison_mode"] == "alias-fallback"
    assert report["alias_fallback"]["fallback_flag"] == "--include-history-update-alias"


def test_history_alias_report_includes_alias_fallback_details(tmp_path: Path) -> None:
    gates = [{"name": "runtime_budget", "required": True, "status": "pass"}]
    profiles = {"local": "pass", "ci": "pass", "strict": "warn"}
    _write_bundle(tmp_path / "default", manifest_compat="pass", profiles=profiles, gates=gates)
    _write_bundle(tmp_path / "alias-fallback", manifest_compat="pass", profiles=profiles, gates=gates)
    manifest = json.loads((tmp_path / "alias-fallback" / "review_bundle_manifest.json").read_text(encoding="utf-8"))
    manifest["history_update"] = {
        "deprecated": True,
        "use": "history",
        "deprecation_stage": "compatibility_alias",
        "consumer_action": "Read manifest.history instead.",
    }
    (tmp_path / "alias-fallback" / "review_bundle_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = build_history_alias_migration_report(
        default_bundle_root=tmp_path / "default",
        no_alias_bundle_root=tmp_path / "alias-fallback",
    )
    assert report["alias_fallback"]["default_emits_alias"] is False
    assert report["alias_fallback"]["fallback_manifest_has_alias"] is True
    assert report["alias_fallback"]["deprecation_stage"] == "compatibility_alias"
