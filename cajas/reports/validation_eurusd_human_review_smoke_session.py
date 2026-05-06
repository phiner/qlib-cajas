"""Validate EURUSD human review smoke-session persistence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_REVIEW_KEYS = [
    "sample_id",
    "human_label",
    "human_confidence",
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
    "review_updated_at_utc",
]
REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
FORBIDDEN_TRADING_FIELDS = {
    "trade_signal",
    "entry",
    "exit",
    "position_size",
    "order",
    "target_position",
}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_read_csv(path: Path) -> tuple[pd.DataFrame | None, str | None]:
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return None, str(exc)


def _safe_read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    bad: list[str] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
            else:
                bad.append(f"line_{i}_not_object")
        except Exception:
            bad.append(f"line_{i}_invalid_json")
    return rows, bad


def _txt(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def build_human_review_smoke_session_report(
    *,
    completed_csv: Path,
    review_events_jsonl: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    trial = _load_json(trial_approval_json) or {}
    trial_status = str(trial.get("status", "not_approved"))

    base = {
        "report_status": "awaiting_smoke_reviews",
        "completed_review_csv_exists": completed_csv.exists(),
        "review_events_jsonl_exists": review_events_jsonl.exists(),
        "reviewed_sample_count": 0,
        "jsonl_event_count": 0,
        "zh_rationale_saved_count": 0,
        "standard_version_saved_count": 0,
        "latest_state_unique_by_sample_id": True,
        "human_label_present_count": 0,
        "human_confidence_present_count": 0,
        "completed_review_csv_path": str(completed_csv),
        "review_events_jsonl_path": str(review_events_jsonl),
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "blocking_reasons": [],
    }

    if trial_status != "not_approved":
        base["report_status"] = "blocked"
        base["real_llm_integration_approved"] = True
        base["blocking_reasons"].append(f"trial_approval_must_be_not_approved:{trial_status}")
        return base

    if not completed_csv.exists() or not review_events_jsonl.exists():
        return base

    completed_df, completed_err = _safe_read_csv(completed_csv)
    if completed_df is None:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"completed_csv_unreadable:{completed_err}")
        return base

    rows, bad = _safe_read_jsonl(review_events_jsonl)
    if bad:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append("events_jsonl_malformed")
        base["blocking_reasons"].extend(bad)
        return base

    missing_keys = [k for k in REQUIRED_REVIEW_KEYS if k not in completed_df.columns]
    if missing_keys:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"missing_required_english_keys:{','.join(missing_keys)}")
        return base

    if any(any(ord(ch) > 127 for ch in c) for c in completed_df.columns):
        base["report_status"] = "blocked"
        base["blocking_reasons"].append("non_english_schema_keys_detected")
        return base

    forbidden_cols = [c for c in completed_df.columns if c.lower() in FORBIDDEN_TRADING_FIELDS]
    if forbidden_cols:
        base["report_status"] = "blocked"
        base["blocking_reasons"].append(f"forbidden_trading_fields_detected:{','.join(sorted(forbidden_cols))}")
        return base

    sample_counts = completed_df["sample_id"].astype(str).value_counts()
    dups = sorted([sid for sid, n in sample_counts.items() if int(n) > 1])
    if dups:
        base["report_status"] = "blocked"
        base["latest_state_unique_by_sample_id"] = False
        base["blocking_reasons"].append(f"duplicate_latest_state_sample_ids:{','.join(dups)}")
        return base

    dedup = completed_df.drop_duplicates(subset=["sample_id"], keep="last").copy()
    reviewed = dedup[_txt(dedup["review_updated_at_utc"]) != ""].copy()

    base["reviewed_sample_count"] = int(len(reviewed))
    base["jsonl_event_count"] = int(len(rows))
    base["zh_rationale_saved_count"] = int((_txt(reviewed["human_rationale_zh"]) != "").sum())
    base["human_label_present_count"] = int((_txt(reviewed["human_label"]) != "").sum())
    base["human_confidence_present_count"] = int((_txt(reviewed["human_confidence"]) != "").sum())

    std_count = 0
    for row in rows:
        review = row.get("review") if isinstance(row.get("review"), dict) else {}
        if str(row.get("standard_version", "")).strip() == "eurusd_15m_review_standard_v0":
            std_count += 1
        elif str(review.get("standard_version", "")).strip() == "eurusd_15m_review_standard_v0":
            std_count += 1
    base["standard_version_saved_count"] = int(std_count)

    if base["reviewed_sample_count"] <= 0 or base["jsonl_event_count"] <= 0:
        base["report_status"] = "awaiting_smoke_reviews"
    elif (
        base["human_label_present_count"] <= 0
        or base["human_confidence_present_count"] <= 0
        or base["zh_rationale_saved_count"] <= 0
        or base["standard_version_saved_count"] <= 0
    ):
        base["report_status"] = "blocked"
        if base["human_label_present_count"] <= 0:
            base["blocking_reasons"].append("missing_saved_human_label")
        if base["human_confidence_present_count"] <= 0:
            base["blocking_reasons"].append("missing_saved_human_confidence")
        if base["zh_rationale_saved_count"] <= 0:
            base["blocking_reasons"].append("missing_saved_human_rationale_zh")
        if base["standard_version_saved_count"] <= 0:
            base["blocking_reasons"].append("missing_saved_standard_version")
    else:
        base["report_status"] = "human_review_smoke_ready"

    return base


def render_human_review_smoke_session_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Human Review Smoke Session",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- completed_review_csv_exists: `{report.get('completed_review_csv_exists')}`",
        f"- review_events_jsonl_exists: `{report.get('review_events_jsonl_exists')}`",
        f"- reviewed_sample_count: `{report.get('reviewed_sample_count')}`",
        f"- jsonl_event_count: `{report.get('jsonl_event_count')}`",
        f"- zh_rationale_saved_count: `{report.get('zh_rationale_saved_count')}`",
        f"- standard_version_saved_count: `{report.get('standard_version_saved_count')}`",
        f"- latest_state_unique_by_sample_id: `{report.get('latest_state_unique_by_sample_id')}`",
        f"- human_label_present_count: `{report.get('human_label_present_count')}`",
        f"- human_confidence_present_count: `{report.get('human_confidence_present_count')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Manual Smoke Steps",
        "",
        "```bash",
        "./scripts/run_eurusd_review_gui.sh",
        "```",
        "- Review 3 to 5 samples.",
        "- Fill human_label, human_confidence, human_rationale_zh.",
        "- Use Save and Save and Next at least once.",
        "- Navigate back and confirm saved values reload.",
        "- Do not reset batch unless explicitly needed.",
        "",
        "## Boundary",
        "",
        "- real LLM integration remains unapproved",
        "- trial approval remains not_approved",
        "- no trading actions",
        "",
        "## Blocking Reasons",
        "",
    ]
    reasons = report.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {item}" for item in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
