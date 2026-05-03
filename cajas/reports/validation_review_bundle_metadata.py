"""Canonical metadata helpers for validation review bundles."""

from typing import Any

HISTORY_STATUS_PASS = "pass"
HISTORY_STATUS_WARN = "warn"
HISTORY_STATUS_FAIL = "fail"


def infer_history_status(recommendation: str, regressions: list[str], history_error: bool = False) -> str:
    """Infer compact history status for reviewer summary."""
    if history_error:
        return HISTORY_STATUS_FAIL
    if recommendation == "review_regressions" or regressions:
        return HISTORY_STATUS_WARN
    return HISTORY_STATUS_PASS


def normalize_history_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return canonical history metadata from either `history` or legacy `history_update`."""
    history = manifest.get("history")
    if isinstance(history, dict) and "enabled" in history:
        return {
            "source": "history",
            "enabled": bool(history.get("enabled", False)),
            "status": history.get("status", "not_requested"),
            "history_jsonl": history.get("history_jsonl"),
            "summary_json": history.get("summary_json"),
            "summary_md": history.get("summary_md"),
            "snapshot_count": int(history.get("snapshot_count", 0) or 0),
            "latest_bundle_status": history.get("latest_bundle_status"),
            "runtime_budget_status": history.get("runtime_budget_status"),
            "regression_count": int(history.get("regression_count", 0) or 0),
            "delta_from_previous": history.get("delta_from_previous") or {},
            "latest_snapshot": history.get("latest_snapshot") or {},
            "regressions": history.get("regressions") or [],
            "reviewer_recommendation": history.get("reviewer_recommendation"),
            "note": history.get("note"),
        }

    legacy = manifest.get("history_update", {})
    requested = bool(legacy.get("requested", False))
    if not requested:
        return {
            "source": "history_update",
            "enabled": False,
            "status": "not_requested",
            "history_jsonl": None,
            "summary_json": None,
            "summary_md": None,
            "snapshot_count": 0,
            "latest_bundle_status": None,
            "runtime_budget_status": manifest.get("runtime_budget_status"),
            "regression_count": 0,
            "delta_from_previous": {},
            "latest_snapshot": {},
            "regressions": [],
            "reviewer_recommendation": None,
            "note": "History update was not requested for this bundle.",
        }

    if legacy.get("status") == "error":
        return {
            "source": "history_update",
            "enabled": True,
            "status": HISTORY_STATUS_FAIL,
            "history_jsonl": legacy.get("history_jsonl"),
            "summary_json": legacy.get("summary_json"),
            "summary_md": legacy.get("summary_md"),
            "snapshot_count": int(legacy.get("snapshot_count", 0) or 0),
            "latest_bundle_status": legacy.get("latest_bundle_status"),
            "runtime_budget_status": manifest.get("runtime_budget_status"),
            "regression_count": int(legacy.get("regression_count", 0) or 0),
            "delta_from_previous": legacy.get("delta_from_previous") or {},
            "latest_snapshot": legacy.get("latest_snapshot") or {},
            "regressions": legacy.get("regressions") or [],
            "reviewer_recommendation": legacy.get("reviewer_recommendation"),
            "note": legacy.get("error"),
        }

    recommendation = str(legacy.get("reviewer_recommendation", ""))
    regressions = legacy.get("regressions") or []
    return {
        "source": "history_update",
        "enabled": True,
        "status": infer_history_status(recommendation, regressions),
        "history_jsonl": legacy.get("history_jsonl"),
        "summary_json": legacy.get("summary_json"),
        "summary_md": legacy.get("summary_md"),
        "snapshot_count": int(legacy.get("snapshot_count", 0) or 0),
        "latest_bundle_status": legacy.get("latest_bundle_status"),
        "runtime_budget_status": manifest.get("runtime_budget_status"),
        "regression_count": int(legacy.get("regression_count", 0) or 0),
        "delta_from_previous": legacy.get("delta_from_previous") or {},
        "latest_snapshot": legacy.get("latest_snapshot") or {},
        "regressions": regressions,
        "reviewer_recommendation": legacy.get("reviewer_recommendation"),
        "note": None,
    }


def validate_history_metadata_compatibility(manifest: dict[str, Any]) -> list[str]:
    """Return lightweight compatibility warnings for canonical/legacy history metadata."""
    warnings: list[str] = []
    history = manifest.get("history")
    legacy = manifest.get("history_update")

    if history is None:
        warnings.append("canonical history field missing")

    if isinstance(legacy, dict):
        if legacy.get("deprecated") is not True:
            warnings.append("history_update is present but deprecated flag is missing or false")
        if legacy.get("use") != "history":
            warnings.append("history_update.use should be 'history'")

    normalized = normalize_history_metadata(manifest)
    if normalized.get("source") == "history_update":
        warnings.append("legacy-only history_update fallback used; migrate producer/consumer to canonical history")

    if isinstance(history, dict) and isinstance(legacy, dict):
        if history.get("enabled") != legacy.get("requested"):
            warnings.append("history.enabled disagrees with history_update.requested")
        if str(history.get("status")) == "pass" and str(legacy.get("status")) == "error":
            warnings.append("history.status and history_update.status disagree")
        if history.get("history_jsonl") and legacy.get("history_jsonl"):
            if history.get("history_jsonl") != legacy.get("history_jsonl"):
                warnings.append("history.history_jsonl disagrees with history_update.history_jsonl")

    return warnings
