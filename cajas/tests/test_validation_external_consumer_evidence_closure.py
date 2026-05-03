import json
from pathlib import Path

from cajas.reports.validation_external_consumer_evidence_closure import (
    build_validation_external_consumer_evidence_closure,
    render_validation_external_consumer_evidence_closure_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_external_consumer_evidence_closure_defaults_to_closed_confirmed(tmp_path: Path) -> None:
    payload = build_validation_external_consumer_evidence_closure(
        alias_post_removal_closure=_write(tmp_path / "alias.json", {"status": "closed", "legacy_read_normalization_kept": True}),
        maintenance_governance_closure=_write(tmp_path / "gov.json", {"status": "ready"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"status": "open", "blocking": False, "items": []}),
    )
    assert payload["status"] == "closed_confirmed"
    assert payload["blocking"] is False
    assert payload["active_alias_emission_supported"] is False


def test_external_consumer_evidence_closure_marks_unresolved_external_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_external_consumer_evidence_closure(
        alias_post_removal_closure=_write(tmp_path / "alias.json", {"status": "closed", "legacy_read_normalization_kept": True}),
        maintenance_governance_closure=_write(tmp_path / "gov.json", {"status": "ready"}),
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        optional_followups_report=_write(tmp_path / "followups.json", {"status": "open", "blocking": False}),
        consumer_owner_handoff=_write(tmp_path / "owner.json", {"status": "open", "handoff_items": [{"consumer": "x", "owner": "external-review-needed"}]}),
    )
    assert payload["status"] == "closed_unresolved_external"
    assert payload["blocking"] is False
    assert payload["remaining_action"] == "external_tracking_only"
    md = render_validation_external_consumer_evidence_closure_markdown(payload)
    assert "Reviewer Next Action" in md
