import json
from pathlib import Path

from cajas.reports.validation_consumer_owner_response import validate_consumer_owner_response


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _base_evidence(tmp_path: Path) -> Path:
    return _write(
        tmp_path / "evidence.json",
        {"consumers": [{"name": "external_unknown_consumer", "owner": "external-review-needed", "status": "unknown"}]},
    )


def test_owner_response_valid_confirmed_clear(tmp_path: Path) -> None:
    evidence = _base_evidence(tmp_path)
    response = _write(
        tmp_path / "response.json",
        {
            "consumer": "external_unknown_consumer",
            "owner": "external-team",
            "status": "confirmed_clear",
            "requires_history_update": False,
            "evidence": "reads manifest.history only",
            "last_checked": "2026-05-03",
            "next_action": "none",
        },
    )
    out_candidate = tmp_path / "updated.json"
    report = validate_consumer_owner_response(
        consumer_evidence=evidence,
        owner_response=response,
        apply_to_out=out_candidate,
    )
    assert report["status"] == "valid_ready_to_apply"
    assert report["safe_to_update_evidence"] is True
    assert out_candidate.exists()


def test_owner_response_valid_requires_alias(tmp_path: Path) -> None:
    evidence = _base_evidence(tmp_path)
    response = _write(
        tmp_path / "response.json",
        {
            "consumer": "external_unknown_consumer",
            "owner": "external-team",
            "status": "requires_alias",
            "requires_history_update": True,
            "evidence": "still reads history_update",
            "last_checked": "2026-05-03",
            "next_action": "migrate_consumer",
        },
    )
    report = validate_consumer_owner_response(consumer_evidence=evidence, owner_response=response)
    assert report["status"] == "valid_requires_alias"
    assert report["safe_to_update_evidence"] is False


def test_owner_response_incomplete_missing_evidence(tmp_path: Path) -> None:
    evidence = _base_evidence(tmp_path)
    response = _write(
        tmp_path / "response.json",
        {
            "consumer": "external_unknown_consumer",
            "owner": "external-team",
            "status": "unknown",
            "requires_history_update": False,
            "evidence": "",
            "last_checked": "2026-05-03",
            "next_action": "identify_owner",
        },
    )
    report = validate_consumer_owner_response(consumer_evidence=evidence, owner_response=response)
    assert report["status"] == "incomplete"


def test_owner_response_invalid_unknown_consumer(tmp_path: Path) -> None:
    evidence = _base_evidence(tmp_path)
    response = _write(
        tmp_path / "response.json",
        {
            "consumer": "not_known",
            "owner": "external-team",
            "status": "confirmed_clear",
            "requires_history_update": False,
            "evidence": "ok",
            "last_checked": "2026-05-03",
            "next_action": "none",
        },
    )
    report = validate_consumer_owner_response(consumer_evidence=evidence, owner_response=response)
    assert report["status"] == "invalid"
    assert "unknown_consumer" in report["issues"]
