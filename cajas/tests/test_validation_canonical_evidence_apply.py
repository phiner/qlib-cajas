import json
from pathlib import Path

from cajas.reports.validation_canonical_evidence_apply import (
    build_canonical_evidence_apply_report,
    render_canonical_evidence_apply_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> dict[str, Path]:
    real = _write(
        tmp_path / "real.json",
        {"consumers": [{"name": "external_unknown_consumer", "status": "unknown"}]},
    )
    candidate = _write(
        tmp_path / "candidate.json",
        {"consumers": [{"name": "external_unknown_consumer", "status": "confirmed_clear"}]},
    )
    plan = _write(tmp_path / "plan.json", {"status": "ready_to_apply", "candidate_valid": True})
    approval = _write(tmp_path / "approval.json", {"approved": True})
    backup = tmp_path / "backup.json"
    out = tmp_path / "applied.json"
    return {"real": real, "candidate": candidate, "plan": plan, "approval": approval, "backup": backup, "out": out}


def test_dry_run_ready_with_approved_inputs(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    payload, _ = build_canonical_evidence_apply_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        canonical_evidence_update_plan=p["plan"],
        approval_file=p["approval"],
        backup_out=p["backup"],
        out_evidence=p["out"],
        dry_run=True,
        apply_in_place=False,
    )
    assert payload["status"] == "dry_run_ready"
    assert p["out"].exists()
    assert payload["diff_summary"]["status_changes"][0]["to"] == "confirmed_clear"


def test_blocked_when_approval_not_true(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    _write(p["approval"], {"approved": False})
    payload, _ = build_canonical_evidence_apply_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        canonical_evidence_update_plan=p["plan"],
        approval_file=p["approval"],
        backup_out=p["backup"],
        out_evidence=p["out"],
        dry_run=True,
        apply_in_place=False,
    )
    assert payload["status"] == "blocked"


def test_blocked_when_update_plan_not_ready(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    _write(p["plan"], {"status": "not_ready", "candidate_valid": True})
    payload, _ = build_canonical_evidence_apply_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        canonical_evidence_update_plan=p["plan"],
        approval_file=p["approval"],
        backup_out=p["backup"],
        out_evidence=p["out"],
        dry_run=True,
        apply_in_place=False,
    )
    assert payload["status"] == "blocked"


def test_markdown_includes_rollback_and_non_goal(tmp_path: Path) -> None:
    p = _inputs(tmp_path)
    payload, _ = build_canonical_evidence_apply_report(
        real_evidence=p["real"],
        candidate_evidence=p["candidate"],
        canonical_evidence_update_plan=p["plan"],
        approval_file=p["approval"],
        backup_out=p["backup"],
        out_evidence=p["out"],
        dry_run=True,
        apply_in_place=False,
    )
    md = render_canonical_evidence_apply_markdown(payload)
    assert "Rollback Plan" in md
    assert "Do not remove alias fallback in this phase." in md
