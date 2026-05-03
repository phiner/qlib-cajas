import json
from pathlib import Path

from cajas.reports.validation_alias_fallback_removal_readiness import (
    build_alias_fallback_removal_readiness,
    render_alias_fallback_removal_readiness_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_alias_fallback_removal_ready_to_schedule(tmp_path: Path) -> None:
    readiness = _write(tmp_path / "readiness.json", {"status": "ready_for_real_apply"})
    removal = _write(tmp_path / "removal.json", {"status": "ready_to_schedule"})
    sunset = _write(tmp_path / "sunset.json", {"status": "ready"})
    report = build_alias_fallback_removal_readiness(
        applied_evidence_readiness=readiness,
        applied_alias_removal_plan=removal,
        applied_alias_sunset_review=sunset,
    )
    assert report["status"] == "ready_to_schedule"
    assert report["do_not_remove_in_this_phase"] is True
    assert report["must_keep"]
    md = render_alias_fallback_removal_readiness_markdown(report)
    assert "must_keep" not in md.lower() or "Must Keep" in md


def test_alias_fallback_removal_not_ready_when_projection_watch(tmp_path: Path) -> None:
    readiness = _write(tmp_path / "readiness.json", {"status": "watch"})
    removal = _write(tmp_path / "removal.json", {"status": "not_ready"})
    sunset = _write(tmp_path / "sunset.json", {"status": "watch"})
    report = build_alias_fallback_removal_readiness(
        applied_evidence_readiness=readiness,
        applied_alias_removal_plan=removal,
        applied_alias_sunset_review=sunset,
    )
    assert report["status"] == "not_ready"
