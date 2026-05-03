import json
from pathlib import Path

from cajas.reports.validation_optional_followups import (
    build_validation_optional_followups,
    render_validation_optional_followups_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_optional_followups_open_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_optional_followups(
        release_readiness_report=_write(tmp_path / "readiness.json", {"status": "ready"}),
        final_reviewer_packet=_write(tmp_path / "reviewer.json", {"status": "ready_for_review"}),
        maintenance_cadence=_write(tmp_path / "cadence.json", {"status": "routine"}),
    )
    assert payload["status"] == "open"
    assert payload["blocking"] is False
    assert len(payload["items"]) == 2
    md = render_validation_optional_followups_markdown(payload)
    assert "Scope Boundary" in md
