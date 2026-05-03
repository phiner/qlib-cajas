import json
from pathlib import Path

from cajas.reports.validation_external_consumer_governance import (
    build_validation_external_consumer_governance,
    render_validation_external_consumer_governance_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_external_consumer_governance_safe_defaults(tmp_path: Path) -> None:
    payload = build_validation_external_consumer_governance()
    assert payload["blocking"] is False
    assert payload["release_readiness_impact"] == "none"


def test_external_consumer_governance_non_blocking_current_followups(tmp_path: Path) -> None:
    payload = build_validation_external_consumer_governance(
        optional_followups=_write(
            tmp_path / "followups.json",
            {
                "status": "open",
                "blocking": False,
                "items": [
                    {"reason": "Alias sunset governance trail still has unresolved external-owner evidence."},
                    {"reason": "Pytest runtime profile may keep warn-level hotspots without blocking release readiness."},
                ],
            },
        ),
        maintenance_governance_closure=_write(tmp_path / "closure.json", {"status": "ready"}),
        alias_post_removal_closure=_write(tmp_path / "alias.json", {"status": "closed", "legacy_read_normalization_kept": True}),
    )
    assert payload["blocking"] is False
    assert payload["release_readiness_impact"] == "none"
    assert payload["alias_producer_behavior"] == "canonical_only"
    assert payload["legacy_read_normalization"] == "preserved"
    md = render_validation_external_consumer_governance_markdown(payload)
    assert "Next Maintenance Action" in md
