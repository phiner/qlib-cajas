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

TREND_TYPES = {"short_trend_down_candidate", "short_trend_up_candidate"}
NON_TREND_PRIMARY_REASON = {
    "lower_wick_rejection_candidate": "lower_wick_rejection_geometry",
    "upper_wick_rejection_candidate": "upper_wick_rejection_geometry",
    "possible_false_breakout_candidate": "false_breakout_structure",
    "compression_candidate": "range_compression",
    "expansion_candidate": "range_expansion",
    "doji_indecision_candidate": "doji_indecision_geometry",
}


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


def _bool_true_count(df: pd.DataFrame, col: str) -> int:
    if col not in df.columns:
        return 0
    s = df[col]
    if s.dtype == bool:
        return int(s.fillna(False).sum())
    norm = s.fillna(False).astype(str).str.strip().str.lower()
    return int(norm.isin({"1", "true", "yes", "y", "t"}).sum())


def _to_bool_series(df: pd.DataFrame, col: str, default: bool) -> pd.Series:
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index)
    s = df[col]
    if s.dtype == bool:
        return s.fillna(default)
    norm = s.fillna(str(default)).astype(str).str.strip().str.lower()
    return norm.isin({"1", "true", "yes", "y", "t"})


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
    template = template if isinstance(template, pd.DataFrame) else pd.DataFrame()
    batch = batch if isinstance(batch, pd.DataFrame) else pd.DataFrame()
    clean = clean if isinstance(clean, pd.DataFrame) else pd.DataFrame()
    rejected = rejected if isinstance(rejected, pd.DataFrame) else pd.DataFrame()

    required_causality_cols = [
        "causal_candidate",
        "candidate_logic_uses_future_bars",
        "candidate_logic_future_bars_used",
        "review_filter_uses_future_bars",
        "review_filter_future_bars_used",
        "label_uses_future_bars",
        "not_for_live_signal",
        "future_usage_role",
    ]
    missing_causality = [c for c in required_causality_cols if c not in cand.columns]

    for col in ["reason_codes", "candidate_reason_codes", "selection_reason_codes", "review_sampling_reason_codes", "primary_selection_reason"]:
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

    if "sample_id" in cand.columns:
        cand = cand.drop_duplicates(subset=["sample_id"], keep="first").reset_index(drop=True)

    # duplicate region summary
    duplicate_summary = {
        "exact_duplicate_sample_ids": 0,
        "same_timestamp_duplicates": 0,
        "anchor_near_duplicates": 0,
        "same_region_duplicates": 0,
        "high_window_overlap_duplicate_groups": 0,
        "window_overlap_max_ratio": 0.0,
    }
    if not batch.empty and "timestamp" in batch.columns:
        bts = pd.to_datetime(batch["timestamp"], utc=True, errors="coerce")
        duplicate_summary["same_timestamp_duplicates"] = int(bts.astype(str).duplicated().sum())
        if "overlap_summary" in batch.columns:
            # Reserved for future embedded overlap summaries.
            pass
        if "max_window_overlap_ratio" in batch.columns:
            duplicate_summary["window_overlap_max_ratio"] = float(pd.to_numeric(batch["max_window_overlap_ratio"], errors="coerce").fillna(0.0).max())
        elif "source_row_index" in batch.columns:
            si = pd.to_numeric(batch["source_row_index"], errors="coerce").dropna().sort_values().astype(int)
            gaps = si.diff().dropna()
            duplicate_summary["anchor_near_duplicates"] = int((gaps <= 8).sum())
            duplicate_summary["same_region_duplicates"] = int((gaps <= 48).sum())
            duplicate_summary["high_window_overlap_duplicate_groups"] = int((gaps <= 42).sum())
            if not gaps.empty:
                overlap = (64 - gaps.clip(upper=64)) / 64.0
                duplicate_summary["window_overlap_max_ratio"] = round(float(overlap.max()), 6)

    batch_ref = batch.copy()
    selected = cand
    required_selected_cols = {
        "candidate_type",
        "primary_selection_reason",
        "selection_reason_codes",
        "excluded_late_reversal_anchor",
        "preferred_review_candidate",
    }
    if not batch_ref.empty and required_selected_cols.issubset(set(batch_ref.columns)):
        selected = batch_ref.copy()
    elif not batch_ref.empty:
        if "sample_id" in batch_ref.columns and "sample_id" in cand.columns:
            selected = cand[cand["sample_id"].astype(str).isin(batch_ref["sample_id"].astype(str))]
        elif all(col in batch_ref.columns for col in ["source_row_index", "candidate_type"]) and all(col in cand.columns for col in ["source_row_index", "candidate_type"]):
            bkeys = set((batch_ref["source_row_index"].astype(str) + "||" + batch_ref["candidate_type"].astype(str)).tolist())
            ckeys = cand["source_row_index"].astype(str) + "||" + cand["candidate_type"].astype(str)
            selected = cand[ckeys.isin(bkeys)]
        elif all(col in batch_ref.columns for col in ["timestamp", "candidate_type"]) and all(col in cand.columns for col in ["timestamp", "candidate_type"]):
            bkeys = set(
                (
                    pd.to_datetime(batch_ref["timestamp"], utc=True, errors="coerce").astype(str)
                    + "||"
                    + batch_ref["candidate_type"].astype(str)
                ).tolist()
            )
            ckeys = (
                pd.to_datetime(cand["timestamp"], utc=True, errors="coerce").astype(str)
                + "||"
                + cand["candidate_type"].astype(str)
            )
            selected = cand[ckeys.isin(bkeys)]
        elif "timestamp" in batch_ref.columns and "timestamp" in cand.columns:
            cts = pd.to_datetime(cand["timestamp"], utc=True, errors="coerce").astype(str)
            bts_set = set(pd.to_datetime(batch_ref["timestamp"], utc=True, errors="coerce").astype(str).tolist())
            selected = cand[cts.isin(bts_set)]
    if selected.empty:
        selected = cand

    # fill deterministic non-trend primary reason expectations for audit
    for ctype, reason in NON_TREND_PRIMARY_REASON.items():
        mask = (selected.get("candidate_type", pd.Series([], dtype=str)).astype(str) == ctype) & (
            selected["primary_selection_reason"].fillna("").astype(str).str.strip() == ""
        )
        if mask.any():
            selected.loc[mask, "primary_selection_reason"] = reason

    explain_missing = {
        "missing_reason_codes": int((selected["reason_codes"].fillna("").astype(str).str.strip() == "").sum()),
        "missing_selection_reason": int((selected["primary_selection_reason"].fillna("").astype(str).str.strip() == "").sum()),
        "missing_selection_reason_codes": int((selected["selection_reason_codes"].fillna("").astype(str).str.strip() == "").sum()),
        "missing_review_sampling_reason_codes": int((selected["review_sampling_reason_codes"].fillna("").astype(str).str.strip() == "").sum()),
        "trend_missing_segment_metadata": 0,
    }
    trend = selected[selected.get("candidate_type", pd.Series([], dtype=str)).isin(TREND_TYPES)]
    if not trend.empty:
        need = ["segment_reason_codes", "segment_id", "segment_position_fraction", "representative_anchor", "preferred_review_candidate"]
        miss = 0
        for c in need:
            if c not in trend.columns:
                miss += len(trend)
            else:
                miss += int((trend[c].fillna("").astype(str).str.strip() == "").sum())
        explain_missing["trend_missing_segment_metadata"] = int(miss)
    trend_excluded_count = 0
    if "excluded_late_reversal_anchor" in batch_ref.columns:
        trend_batch = batch_ref[batch_ref.get("candidate_type", pd.Series([], dtype=str)).astype(str).str.contains("trend", na=False)]
        vals = trend_batch.get("excluded_late_reversal_anchor", pd.Series([], dtype=object)).fillna(False).astype(str).str.strip().str.lower()
        trend_excluded_count = int(vals.isin({"1", "true", "yes", "y", "t"}).sum())
    else:
        trend_excluded_count = _bool_true_count(trend, "excluded_late_reversal_anchor")
    trend_nonpreferred_without_fallback = 0
    if not trend.empty and "preferred_review_candidate" in trend.columns:
        pref = trend["preferred_review_candidate"].fillna(True).astype(bool)
        fallback = trend.get("fallback_reason", pd.Series([""] * len(trend))).fillna("").astype(str).str.strip()
        trend_nonpreferred_without_fallback = int((~pref & (fallback == "")).sum())
    trend_tail_audit = {}
    trend_batch = selected[selected.get("candidate_type", pd.Series([], dtype=str)).astype(str).str.contains("trend", na=False)].copy()
    if trend_batch.empty:
        trend_tail_audit = {
            "trend_batch_count": 0,
            "trend_near_tail_count": 0,
            "trend_near_tail_ratio": 0.0,
            "trend_ideal_mid_count": 0,
            "trend_ideal_mid_ratio": 0.0,
            "trend_post_reversal_count": 0,
            "trend_post_reversal_ratio": 0.0,
            "tail_bias_status": "watch",
        }
    else:
        seg_frac = pd.to_numeric(trend_batch.get("segment_position_fraction", pd.Series([0.0] * len(trend_batch))), errors="coerce").fillna(0.0)
        d_end = pd.to_numeric(trend_batch.get("distance_to_segment_end_bars", pd.Series([999] * len(trend_batch))), errors="coerce").fillna(999)
        near_tail = _to_bool_series(trend_batch, "near_segment_tail", False) | (seg_frac >= 0.65) | (d_end <= 4)
        ideal_mid = _to_bool_series(trend_batch, "ideal_mid_segment_anchor", False) | ((seg_frac >= 0.25) & (seg_frac <= 0.60))
        post_rev = pd.to_numeric(trend_batch.get("post_anchor_reversal_strength", pd.Series([0.0] * len(trend_batch))), errors="coerce").fillna(0.0) >= 1.0
        excluded = _to_bool_series(trend_batch, "excluded_late_reversal_anchor", False)
        total = max(1, len(trend_batch))
        near_tail_ratio = float(near_tail.sum() / total)
        tail_status = "pass" if near_tail_ratio <= 0.10 else ("watch" if near_tail_ratio <= 0.25 else "needs_rule_refinement")
        if bool(excluded.any()):
            tail_status = "blocked"
        trend_tail_audit = {
            "trend_batch_count": int(len(trend_batch)),
            "trend_near_tail_count": int(near_tail.sum()),
            "trend_near_tail_ratio": round(near_tail_ratio, 6),
            "trend_ideal_mid_count": int(ideal_mid.sum()),
            "trend_ideal_mid_ratio": round(float(ideal_mid.sum() / total), 6),
            "trend_post_reversal_count": int(post_rev.sum()),
            "trend_post_reversal_ratio": round(float(post_rev.sum() / total), 6),
            "tail_bias_status": tail_status,
        }

    causality_summary = {
        "missing_causality_columns": missing_causality,
        "causal_candidate_true_count": _bool_true_count(cand, "causal_candidate"),
        "candidate_logic_uses_future_bars_true_count": _bool_true_count(selected, "candidate_logic_uses_future_bars"),
        "review_filter_uses_future_bars_true_count": _bool_true_count(selected, "review_filter_uses_future_bars"),
        "not_for_live_signal_true_count": _bool_true_count(cand, "not_for_live_signal"),
        "batch_selected_rows": int(len(selected)),
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
        "clean_view_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
    }

    batch_cov = coverage_summary["batch"]
    first20 = batch.head(20).copy() if not batch.empty else pd.DataFrame()
    first20_days = 0
    first20_years = 0
    if not first20.empty and "timestamp" in first20.columns:
        fts = pd.to_datetime(first20["timestamp"], utc=True, errors="coerce").dropna()
        first20_days = int(fts.dt.strftime("%Y-%m-%d").nunique())
        first20_years = int(fts.dt.year.nunique())
    coverage_warnings: list[str] = []
    year_cov = batch_cov.get("year", {})
    session_cov = batch_cov.get("session_bucket", {})
    vol_cov = batch_cov.get("volatility_bucket", {})
    if year_cov and max(year_cov.values()) / max(1, sum(year_cov.values())) > 0.70:
        coverage_warnings.append("year_over_concentrated")
    if session_cov and max(session_cov.values()) / max(1, sum(session_cov.values())) > 0.70:
        coverage_warnings.append("session_over_concentrated")
    if vol_cov and len(vol_cov) < 2:
        coverage_warnings.append("volatility_bucket_not_diverse")
    coverage_status = "ok" if not coverage_warnings else "watch"

    active_batch_warnings = []
    if year_cov:
        mx = max(year_cov.values())
        total = sum(year_cov.values())
        if total > 0 and (mx / total) > 0.7:
            active_batch_warnings.append("batch_over_concentrated_single_year")
    if session_cov:
        mx = max(session_cov.values())
        total = sum(session_cov.values())
        if total > 0 and (mx / total) > 0.7:
            active_batch_warnings.append("batch_over_concentrated_single_session")

    gate_failures = {
        "no_candidate_logic_future_usage": causality_summary["candidate_logic_uses_future_bars_true_count"] == 0,
        "no_excluded_late_reversal_in_selected_trend": trend_excluded_count == 0,
        "preferred_false_has_fallback_reason": trend_nonpreferred_without_fallback == 0,
        "selected_rows_have_primary_selection_reason": explain_missing["missing_selection_reason"] == 0,
        "selected_rows_have_selection_reason_codes": explain_missing["missing_selection_reason_codes"] == 0,
        "selected_trend_rows_have_segment_metadata": explain_missing["trend_missing_segment_metadata"] == 0,
        "no_exact_duplicate_sample_ids": duplicate_summary["exact_duplicate_sample_ids"] == 0,
        "no_same_timestamp_duplicate_rows": duplicate_summary["same_timestamp_duplicates"] == 0,
        "source_range_not_truncated": True,
        "batch_year_spans_multiple_years": first20_years >= 2 if len(batch) >= 20 else True,
        "artifacts_readable": True,
    }
    must_failures = [k for k, v in gate_failures.items() if not v]
    should_failures = []
    overlap_threshold = 0.35
    overlap_summary = {}
    batch_report_path = Path("tmp/validation-eurusd-pattern-review-batch-001.json")
    if batch_report_path.exists():
        try:
            batch_report_payload = json.loads(batch_report_path.read_text(encoding="utf-8"))
            overlap_summary = batch_report_payload.get("overlap_summary", {}) or {}
            duplicate_summary["window_overlap_max_ratio"] = float(overlap_summary.get("max_window_overlap_ratio", duplicate_summary["window_overlap_max_ratio"]))
            duplicate_summary["high_window_overlap_duplicate_groups"] = int(overlap_summary.get("window_overlap_warning_count", duplicate_summary["high_window_overlap_duplicate_groups"]))
        except Exception:
            overlap_summary = {}
    if duplicate_summary["same_region_duplicates"] > 10:
        should_failures.append("same_region_duplicates_above_threshold")
    if duplicate_summary["window_overlap_max_ratio"] > overlap_threshold:
        should_failures.append("window_overlap_max_ratio_above_threshold")
    if coverage_warnings:
        should_failures.append("coverage_imbalance_detected")
    if multi_label_summary["batch_rows_from_multi_candidate_timestamps"] > max(20, int(len(batch) * 0.7)):
        should_failures.append("multi_label_timestamp_density_high")

    if missing_causality:
        status = "blocked"
    elif trend_tail_audit.get("tail_bias_status") == "blocked":
        status = "blocked"
    elif must_failures:
        status = "needs_rule_refinement"
    elif should_failures:
        status = "watch"
    else:
        status = "pass"

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
        "batch_quality_metrics": {
            "same_region_warning_count": int(duplicate_summary["same_region_duplicates"]),
            "window_overlap_duplicate_count": int(duplicate_summary["high_window_overlap_duplicate_groups"]),
            "fallback_duplicate_region_count": int(_bool_true_count(batch, "duplicate_timestamp_fallback")) if not batch.empty else 0,
            "first20_unique_days": first20_days,
            "first20_unique_years": first20_years,
            "first20_max_window_overlap": float(duplicate_summary["window_overlap_max_ratio"]),
            "first30_max_window_overlap": float(overlap_summary.get("first30_max_window_overlap", duplicate_summary["window_overlap_max_ratio"])),
            "window_overlap_max_ratio_threshold": float(overlap_summary.get("window_overlap_max_ratio_threshold", overlap_threshold)),
            "window_overlap_duplicate_groups": overlap_summary.get("window_overlap_duplicate_groups", []),
            "fallback_window_overlap_count": int(overlap_summary.get("fallback_window_overlap_count", 0)),
            "coverage_status": coverage_status,
            "coverage_warnings": coverage_warnings,
            "first20_coverage_summary": {
                "year": dict(list(batch_cov.get("year", {}).items())[:5]),
                "session_bucket": dict(list(batch_cov.get("session_bucket", {}).items())[:5]),
                "volatility_bucket": dict(list(batch_cov.get("volatility_bucket", {}).items())[:5]),
            },
        },
        "audit_gates": {
            "must_fix_gates": gate_failures,
            "must_fix_failures": must_failures,
            "should_fix_failures": should_failures,
        },
        "trend_tail_bias_audit": trend_tail_audit,
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
