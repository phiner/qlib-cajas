"""EURUSD candidate causality, explainability, conflicts, duplicates, and coverage audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

SESSION_BUCKETS = [
    (0, 7, "asia"),
    (7, 12, "london"),
    (12, 16, "overlap"),
    (16, 21, "new_york"),
    (21, 24, "off_hours"),
]


def _session_bucket(hour: int) -> str:
    for start, end, label in SESSION_BUCKETS:
        if start <= int(hour) < end:
            return label
    return "off_hours"


def _load_csv(path: Path, required: bool) -> tuple[pd.DataFrame | None, str | None]:
    if not path.exists():
        return (None, "missing") if required else (pd.DataFrame(), None)
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return None, str(exc)


def _coverage(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "timestamp" not in df.columns:
        return {
            "year": {}, "month": {}, "weekday": {}, "hour_of_day_utc": {}, "session_bucket": {}, "volatility_bucket": {},
        }
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    ranges = pd.to_numeric(df.get("range", pd.Series([0] * len(df))), errors="coerce").fillna(0.0)
    bins = pd.qcut(ranges.rank(method="first"), q=3, labels=["low", "medium", "high"], duplicates="drop") if len(ranges) > 2 else pd.Series(["medium"] * len(df))
    out_df = pd.DataFrame({"ts": ts, "vol": bins})
    out_df = out_df.dropna(subset=["ts"])
    out_df["year"] = out_df["ts"].dt.year.astype(str)
    out_df["month"] = out_df["ts"].dt.strftime("%Y-%m")
    out_df["weekday"] = out_df["ts"].dt.day_name()
    out_df["hour_of_day_utc"] = out_df["ts"].dt.hour.astype(str)
    out_df["session_bucket"] = out_df["ts"].dt.hour.map(_session_bucket)
    return {
        "year": {str(k): int(v) for k, v in out_df["year"].value_counts().to_dict().items()},
        "month": {str(k): int(v) for k, v in out_df["month"].value_counts().to_dict().items()},
        "weekday": {str(k): int(v) for k, v in out_df["weekday"].value_counts().to_dict().items()},
        "hour_of_day_utc": {str(k): int(v) for k, v in out_df["hour_of_day_utc"].value_counts().to_dict().items()},
        "session_bucket": {str(k): int(v) for k, v in out_df["session_bucket"].value_counts().to_dict().items()},
        "volatility_bucket": {str(k): int(v) for k, v in pd.Series(out_df["vol"]).astype(str).value_counts().to_dict().items()},
    }


def build_validation_eurusd_candidate_audit(
    *,
    candidate_csv: Path,
    template_csv: Path,
    batch_csv: Path,
    clean_view_csv: Path,
    rejected_csv: Path,
) -> dict[str, Any]:
    cand, err = _load_csv(candidate_csv, required=True)
    if cand is None:
        return {
            "status": "blocked",
            "reason": "candidate_csv_missing_or_unreadable",
            "error": err,
            "candidate_csv": str(candidate_csv),
        }

    template, _ = _load_csv(template_csv, required=False)
    batch, _ = _load_csv(batch_csv, required=False)
    clean, _ = _load_csv(clean_view_csv, required=False)
    rejected, _ = _load_csv(rejected_csv, required=False)

    required_causality_cols = [
        "causal_candidate",
        "candidate_logic_uses_future_bars",
        "candidate_logic_future_bars_used",
        "review_filter_uses_future_bars",
        "review_filter_future_bars_used",
        "label_uses_future_bars",
        "not_for_live_signal",
    ]
    missing_causality = [c for c in required_causality_cols if c not in cand.columns]

    for col in ["reason_codes", "candidate_reason_codes", "selection_reason_codes", "primary_selection_reason"]:
        if col not in cand.columns:
            cand[col] = ""

    ts = pd.to_datetime(cand.get("timestamp", pd.Series([], dtype=str)), utc=True, errors="coerce")
    ts_group = cand.assign(_ts=ts.astype(str)).groupby("_ts") if not cand.empty else None
    same_ts_count = {}
    if ts_group is not None:
        same_ts_count = {
            k: sorted(set(v["candidate_type"].astype(str).tolist()))
            for k, v in ts_group
            if len(set(v["candidate_type"].astype(str).tolist())) > 1 and k != "NaT"
        }

    if "same_timestamp_candidate_type_count" not in cand.columns:
        cand["same_timestamp_candidate_type_count"] = 1
    if "same_timestamp_candidate_types" not in cand.columns:
        cand["same_timestamp_candidate_types"] = ""
    if "primary_candidate_type" not in cand.columns:
        cand["primary_candidate_type"] = cand.get("candidate_type", "")
    if "multi_candidate_timestamp" not in cand.columns:
        cand["multi_candidate_timestamp"] = False

    ts_key = ts.astype(str)
    for i in range(len(cand)):
        key = ts_key.iloc[i] if i < len(ts_key) else "NaT"
        types = same_ts_count.get(key, [])
        if types:
            cand.at[i, "same_timestamp_candidate_type_count"] = int(len(types))
            cand.at[i, "same_timestamp_candidate_types"] = "|".join(types)
            cand.at[i, "multi_candidate_timestamp"] = True
            cand.at[i, "primary_candidate_type"] = types[0]

    # duplicate region summary
    duplicate_summary = {
        "exact_duplicate_sample_ids": 0,
        "same_timestamp_duplicates": 0,
        "anchor_near_duplicates": 0,
        "same_region_duplicates": 0,
        "high_window_overlap_duplicate_groups": 0,
    }
    if not batch.empty and "timestamp" in batch.columns:
        bts = pd.to_datetime(batch["timestamp"], utc=True, errors="coerce")
        duplicate_summary["same_timestamp_duplicates"] = int(bts.astype(str).duplicated().sum())
        if "source_row_index" in batch.columns:
            si = pd.to_numeric(batch["source_row_index"], errors="coerce").dropna().sort_values().astype(int)
            gaps = si.diff().dropna()
            duplicate_summary["anchor_near_duplicates"] = int((gaps <= 8).sum())
            duplicate_summary["same_region_duplicates"] = int((gaps <= 48).sum())
            duplicate_summary["high_window_overlap_duplicate_groups"] = int((gaps <= 42).sum())

    explain_missing = {
        "missing_reason_codes": int((cand["reason_codes"].fillna("").astype(str).str.strip() == "").sum()),
        "missing_selection_reason": int((cand["primary_selection_reason"].fillna("").astype(str).str.strip() == "").sum()),
        "trend_missing_segment_metadata": 0,
    }
    trend = cand[cand.get("candidate_type", pd.Series([], dtype=str)).isin(["short_trend_down_candidate", "short_trend_up_candidate"])]
    if not trend.empty:
        need = ["segment_id", "segment_start_timestamp", "segment_end_timestamp"]
        miss = 0
        for c in need:
            if c not in trend.columns:
                miss += len(trend)
            else:
                miss += int((trend[c].fillna("").astype(str).str.strip() == "").sum())
        explain_missing["trend_missing_segment_metadata"] = int(miss)

    causality_summary = {
        "missing_causality_columns": missing_causality,
        "causal_candidate_true_count": int(cand.get("causal_candidate", pd.Series([], dtype=bool)).fillna(False).astype(bool).sum()) if "causal_candidate" in cand.columns else 0,
        "candidate_logic_uses_future_bars_true_count": int(cand.get("candidate_logic_uses_future_bars", pd.Series([], dtype=bool)).fillna(False).astype(bool).sum()) if "candidate_logic_uses_future_bars" in cand.columns else 0,
        "review_filter_uses_future_bars_true_count": int(cand.get("review_filter_uses_future_bars", pd.Series([], dtype=bool)).fillna(False).astype(bool).sum()) if "review_filter_uses_future_bars" in cand.columns else 0,
        "not_for_live_signal_true_count": int(cand.get("not_for_live_signal", pd.Series([], dtype=bool)).fillna(False).astype(bool).sum()) if "not_for_live_signal" in cand.columns else 0,
    }

    future_usage_summary = {
        "future_usage_role_distribution": {
            str(k): int(v)
            for k, v in cand.get("future_usage_role", pd.Series([], dtype=str)).fillna("none").astype(str).value_counts().to_dict().items()
        },
        "review_filter_future_bars_used_max": int(pd.to_numeric(cand.get("review_filter_future_bars_used", pd.Series([0])), errors="coerce").fillna(0).max()) if not cand.empty else 0,
        "candidate_logic_future_bars_used_max": int(pd.to_numeric(cand.get("candidate_logic_future_bars_used", pd.Series([0])), errors="coerce").fillna(0).max()) if not cand.empty else 0,
    }

    multi_label_summary = {
        "timestamps_with_multiple_candidate_types": int(len(same_ts_count)),
        "max_candidate_types_on_one_timestamp": int(max([len(v) for v in same_ts_count.values()], default=0)),
        "top_multi_candidate_timestamps": [
            {"timestamp": k, "candidate_types": v, "count": len(v)}
            for k, v in list(sorted(same_ts_count.items(), key=lambda item: len(item[1]), reverse=True))[:10]
        ],
        "batch_rows_from_multi_candidate_timestamps": int(
            0 if batch.empty or "timestamp" not in batch.columns else pd.to_datetime(batch["timestamp"], utc=True, errors="coerce").astype(str).isin(set(same_ts_count.keys())).sum()
        ),
        "batch_same_timestamp_duplicate_count": duplicate_summary["same_timestamp_duplicates"],
    }

    coverage_summary = {
        "candidate": _coverage(cand),
        "template": _coverage(template if template is not None else pd.DataFrame()),
        "batch": _coverage(batch if batch is not None else pd.DataFrame()),
        "clean_view_rows": int(0 if clean is None else len(clean)),
        "rejected_rows": int(0 if rejected is None else len(rejected)),
    }

    active_batch_warnings = []
    batch_cov = coverage_summary["batch"]
    year_cov = batch_cov.get("year", {})
    if year_cov:
        mx = max(year_cov.values())
        total = sum(year_cov.values())
        if total > 0 and (mx / total) > 0.7:
            active_batch_warnings.append("batch_over_concentrated_single_year")
    session_cov = batch_cov.get("session_bucket", {})
    if session_cov:
        mx = max(session_cov.values())
        total = sum(session_cov.values())
        if total > 0 and (mx / total) > 0.7:
            active_batch_warnings.append("batch_over_concentrated_single_session")

    status = "pass"
    if missing_causality or explain_missing["missing_reason_codes"] > 0 or explain_missing["missing_selection_reason"] > 0:
        status = "watch"
    if explain_missing["trend_missing_segment_metadata"] > 0:
        status = "needs_rule_refinement"

    next_actions = []
    if missing_causality:
        next_actions.append("fill_missing_causality_fields")
    if multi_label_summary["timestamps_with_multiple_candidate_types"] > 0:
        next_actions.append("review_multi_candidate_timestamp_policy")
    if duplicate_summary["same_region_duplicates"] > 0:
        next_actions.append("tighten_same_region_sampling")
    if not next_actions:
        next_actions.append("continue_review_with_current_audit_controls")

    return {
        "status": status,
        "input_paths": {
            "candidate_csv": str(candidate_csv),
            "template_csv": str(template_csv),
            "batch_csv": str(batch_csv),
            "clean_view_csv": str(clean_view_csv),
            "rejected_csv": str(rejected_csv),
        },
        "causality_summary": causality_summary,
        "future_usage_summary": future_usage_summary,
        "selection_explainability_summary": explain_missing,
        "multi_label_summary": multi_label_summary,
        "duplicate_region_summary": duplicate_summary,
        "coverage_summary": coverage_summary,
        "active_batch_warnings": sorted(set(active_batch_warnings)),
        "next_actions": next_actions,
        "scope_boundary": {
            "read_only_audit": True,
            "reset_or_rebuild_performed": False,
            "trading_signal": False,
            "order_generation": False,
        },
    }


def render_validation_eurusd_candidate_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Candidate Audit",
        "",
        f"- status: `{payload.get('status')}`",
        "",
        "## Causality Summary",
        "",
    ]
    for k, v in (payload.get("causality_summary") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(["", "## Future Usage Summary", ""])
    for k, v in (payload.get("future_usage_summary") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(["", "## Selection Explainability", ""])
    for k, v in (payload.get("selection_explainability_summary") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(["", "## Multi Label Summary", ""])
    for k, v in (payload.get("multi_label_summary") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(["", "## Duplicate Region Summary", ""])
    for k, v in (payload.get("duplicate_region_summary") or {}).items():
        lines.append(f"- `{k}`: `{v}`")
    lines.extend(["", "## Active Batch Warnings", ""])
    for w in payload.get("active_batch_warnings", []):
        lines.append(f"- `{w}`")
    lines.extend(["", "## Next Actions", ""])
    for a in payload.get("next_actions", []):
        lines.append(f"- `{a}`")
    lines.extend(["", "## Policy", "", "- Read-only candidate audit.", "- No destructive reset/rebuild.", "- No trading signals/orders.", ""])
    return "\n".join(lines)
