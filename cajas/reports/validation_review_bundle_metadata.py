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


def validate_history_metadata_compatibility(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return compatibility issues with severity for canonical/legacy history metadata."""
    issues: list[dict[str, str]] = []
    history = manifest.get("history")
    legacy = manifest.get("history_update")

    def add_issue(severity: str, code: str, message: str) -> None:
        issues.append({"severity": severity, "code": code, "message": message})

    if history is None:
        add_issue("warning", "canonical_history_missing", "canonical history field missing")
    elif not isinstance(history, dict):
        add_issue("error", "canonical_history_invalid_type", "canonical history field is not an object")
    else:
        history_enabled = bool(history.get("enabled", False))
        if history_enabled:
            for field in ("status", "history_jsonl", "summary_json", "summary_md"):
                if not history.get(field):
                    add_issue("error", "canonical_history_missing_required_field", f"history.{field} is required when history.enabled=true")
        elif not history.get("status"):
            add_issue("warning", "canonical_history_missing_status", "history.status is recommended when history.enabled=false")

    if isinstance(legacy, dict):
        if legacy.get("deprecated") is not True:
            add_issue("warning", "legacy_alias_not_marked_deprecated", "history_update is present but deprecated flag is missing or false")
        legacy_use = legacy.get("use")
        if legacy_use is not None and legacy_use != "history":
            add_issue("error", "legacy_alias_use_mismatch", "history_update.use should be 'history'")
        if legacy_use is None:
            add_issue("warning", "legacy_alias_use_missing", "history_update.use is missing; expected 'history'")
        else:
            add_issue("info", "legacy_alias_present", "deprecated history_update alias is present during compatibility window")

    normalized = normalize_history_metadata(manifest)
    if normalized.get("source") == "history_update":
        add_issue("warning", "legacy_fallback_used", "legacy-only history_update fallback used; migrate producer/consumer to canonical history")

    if isinstance(history, dict) and isinstance(legacy, dict):
        legacy_status = str(legacy.get("status") or "")
        normalized_legacy_status = (
            "pass" if legacy_status == "ok" else "fail" if legacy_status == "error" else legacy_status
        )
        if history.get("enabled") != legacy.get("requested"):
            add_issue("error", "canonical_legacy_enabled_mismatch", "history.enabled disagrees with history_update.requested")
        if history.get("status") and normalized_legacy_status and str(history.get("status")) != normalized_legacy_status:
            add_issue("error", "canonical_legacy_status_mismatch", "history.status disagrees with history_update.status")
        for field in ("history_jsonl", "summary_json", "summary_md"):
            canonical_value = history.get(field)
            legacy_value = legacy.get(field)
            if canonical_value and legacy_value and canonical_value != legacy_value:
                add_issue("error", "canonical_legacy_path_mismatch", f"history.{field} disagrees with history_update.{field}")

    return issues


def summarize_compatibility_issues(issues: list[dict[str, str]]) -> dict[str, Any]:
    """Summarize issue severities into status/counts."""
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    info_count = sum(1 for issue in issues if issue.get("severity") == "info")
    if error_count > 0:
        status = "fail"
    elif warning_count > 0:
        status = "warn"
    else:
        status = "pass"
    return {
        "status": status,
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
    }
