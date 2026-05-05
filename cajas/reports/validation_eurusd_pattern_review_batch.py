"""EURUSD 15m pattern review batch builder report."""
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional, Set

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
]


def diversify_review_samples(
    candidates: pd.DataFrame,
    *,
    target_count: int = 100,
    min_gap_bars: int = 8,
    expected_interval_minutes: int = 15,
    max_samples_per_day: int = 8,
    balanced_by_candidate_type: bool = True,
    anchor_duplicate_gap_bars: int = 8,
    same_region_cooldown_bars: int = 48,
    window_bars: int = 120,
    pre_context_ratio: float = 0.6,
    window_overlap_max_ratio: float = 0.35,
) -> pd.DataFrame:
    """Build a diversified sample set with graceful fallback."""
    if candidates.empty:
        return candidates.copy()
    df = candidates.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).reset_index(drop=True)
    if df.empty:
        return df
    df["_day"] = df["timestamp"].dt.strftime("%Y-%m-%d")
    gap_minutes = int(min_gap_bars) * int(expected_interval_minutes)

    pre_bars = int(round(window_bars * pre_context_ratio))
    post_bars = max(0, int(window_bars) - pre_bars)

    def _anchor(row: pd.Series) -> int:
        return int(pd.to_numeric(row.get("source_row_index", -1), errors="coerce"))

    def _window(row: pd.Series) -> tuple[int, int]:
        a = _anchor(row)
        return a - pre_bars, a + post_bars

    def _overlap_ratio(w1: tuple[int, int], w2: tuple[int, int]) -> float:
        lo = max(w1[0], w2[0])
        hi = min(w1[1], w2[1])
        overlap = max(0, hi - lo + 1)
        denom = max(1, window_bars)
        return float(overlap / denom)

    def _passes_constraints(row: pd.Series, selected_rows: list[pd.Series], per_day: dict[str, int], enforce_gap: bool, enforce_day_cap: bool, enforce_overlap: bool) -> bool:
        day = str(row["_day"])
        if enforce_day_cap and per_day.get(day, 0) >= int(max_samples_per_day):
            return False
        t = row["timestamp"]
        row_anchor = _anchor(row)
        row_win = _window(row)
        if enforce_gap and selected_rows:
            for s in selected_rows:
                if abs((t - s["timestamp"]).total_seconds()) / 60.0 < gap_minutes:
                    return False
                s_anchor = _anchor(s)
                if row_anchor >= 0 and s_anchor >= 0:
                    if abs(row_anchor - s_anchor) < int(anchor_duplicate_gap_bars):
                        return False
                    if abs(row_anchor - s_anchor) < int(same_region_cooldown_bars):
                        return False
                if enforce_overlap and row_anchor >= 0 and s_anchor >= 0:
                    if _overlap_ratio(row_win, _window(s)) > float(window_overlap_max_ratio):
                        return False
        return True

    sorted_df = df.sort_values(by=["review_priority", "confidence_score", "timestamp"], ascending=[True, False, True]).reset_index(drop=True)
    selected: list[pd.Series] = []
    used_ids: set[str] = set()
    per_day: dict[str, int] = {}
    # For full-size review batches we prioritize strict anti-overlap constraints.
    # Fallback stages are enabled only for small pools or small target requests.
    strict_only = int(target_count) >= 100
    stages = [
        (True, True, True, bool(balanced_by_candidate_type), ""),
        (True, False, True, bool(balanced_by_candidate_type), "day_cap_relaxed"),
    ]
    if not strict_only:
        stages.extend(
            [
                (True, False, False, bool(balanced_by_candidate_type), "overlap_relaxed"),
                (False, False, False, bool(balanced_by_candidate_type), "gap_relaxed"),
                (False, False, False, False, "balance_relaxed"),
            ]
        )
    else:
        stages.extend(
            [
                (False, False, True, bool(balanced_by_candidate_type), "gap_relaxed"),
                (False, False, True, False, "balance_relaxed"),
            ]
        )

    for enforce_gap, enforce_day_cap, enforce_overlap, enforce_balance, fallback_reason in stages:
        if len(selected) >= min(int(target_count), len(sorted_df)):
            break
        if enforce_balance:
            grouped: dict[str, list[int]] = {}
            for idx, row in sorted_df.iterrows():
                ctype = str(row["candidate_type"])
                grouped.setdefault(ctype, []).append(idx)
            cursors = {k: 0 for k in grouped}
            progressed = True
            while progressed and len(selected) < min(int(target_count), len(sorted_df)):
                progressed = False
                for ctype in sorted(grouped.keys()):
                    cur = cursors[ctype]
                    indices = grouped[ctype]
                    while cur < len(indices):
                        row = sorted_df.iloc[indices[cur]]
                        cur += 1
                        sid = str(row.get("sample_id", f"row_{indices[cur-1]}"))
                        if sid in used_ids:
                            continue
                        if not _passes_constraints(row, selected, per_day, enforce_gap, enforce_day_cap, enforce_overlap):
                            continue
                        row = row.copy()
                        row["fallback_reason"] = fallback_reason
                        row["fallback_window_overlap"] = bool(fallback_reason == "overlap_relaxed")
                        selected.append(row)
                        used_ids.add(sid)
                        per_day[str(row["_day"])] = per_day.get(str(row["_day"]), 0) + 1
                        progressed = True
                        break
                    cursors[ctype] = cur
        else:
            for _, row in sorted_df.iterrows():
                if len(selected) >= min(int(target_count), len(sorted_df)):
                    break
                sid = str(row.get("sample_id", f"row_{_}"))
                if sid in used_ids:
                    continue
                if not _passes_constraints(row, selected, per_day, enforce_gap, enforce_day_cap, enforce_overlap):
                    continue
                row = row.copy()
                row["fallback_reason"] = fallback_reason
                row["fallback_window_overlap"] = bool(fallback_reason == "overlap_relaxed")
                selected.append(row)
                used_ids.add(sid)
                per_day[str(row["_day"])] = per_day.get(str(row["_day"]), 0) + 1

    if not selected:
        return sorted_df.head(target_count).drop(columns=["_day"], errors="ignore").reset_index(drop=True)
    out = pd.DataFrame(selected).drop(columns=["_day"], errors="ignore").reset_index(drop=True)
    return out.head(target_count)


def summarize_sample_time_diversity(samples: pd.DataFrame, timestamp_col: str = "timestamp") -> dict[str, Any]:
    """Summarize time diversity and local clustering."""
    if timestamp_col not in samples.columns:
        return {
            "status": "blocked",
            "sample_count": int(len(samples)),
            "unique_days": 0,
            "max_samples_per_day": 0,
            "min_gap_minutes": None,
            "median_gap_minutes": None,
            "cluster_warning_count": 0,
            "clustered_sample_pairs": [],
        }
    ts = pd.to_datetime(samples[timestamp_col], utc=True, errors="coerce").dropna().sort_values()
    if ts.empty:
        return {
            "status": "blocked",
            "sample_count": int(len(samples)),
            "unique_days": 0,
            "max_samples_per_day": 0,
            "min_gap_minutes": None,
            "median_gap_minutes": None,
            "cluster_warning_count": 0,
            "clustered_sample_pairs": [],
        }
    gaps = ts.diff().dropna().dt.total_seconds() / 60.0
    min_gap = float(gaps.min()) if not gaps.empty else None
    median_gap = float(gaps.median()) if not gaps.empty else None
    days = ts.dt.strftime("%Y-%m-%d")
    counts = days.value_counts()
    max_per_day = int(counts.max()) if not counts.empty else 0
    clustered_pairs = []
    cluster_count = 0
    threshold = 8 * 15
    for i in range(len(ts) - 1):
        gm = float((ts.iloc[i + 1] - ts.iloc[i]).total_seconds() / 60.0)
        if gm < threshold:
            cluster_count += 1
            if len(clustered_pairs) < 8:
                clustered_pairs.append(
                    {
                        "start_timestamp": str(ts.iloc[i]),
                        "end_timestamp": str(ts.iloc[i + 1]),
                        "gap_minutes": gm,
                    }
                )
    status = "diverse" if cluster_count == 0 else "warning"
    return {
        "status": status,
        "sample_count": int(len(ts)),
        "unique_days": int(days.nunique()),
        "max_samples_per_day": max_per_day,
        "min_gap_minutes": min_gap,
        "median_gap_minutes": median_gap,
        "cluster_warning_count": cluster_count,
        "clustered_sample_pairs": clustered_pairs,
    }


def summarize_window_overlap(
    samples: pd.DataFrame,
    *,
    window_bars: int = 120,
    pre_context_ratio: float = 0.6,
    overlap_threshold: float = 0.35,
) -> dict[str, Any]:
    if samples.empty or "source_row_index" not in samples.columns:
        return {
            "window_overlap_max_ratio_threshold": float(overlap_threshold),
            "max_window_overlap_ratio": 0.0,
            "window_overlap_warning_count": 0,
            "window_overlap_duplicate_groups": [],
            "fallback_window_overlap_count": 0,
            "first20_max_window_overlap": 0.0,
            "first30_max_window_overlap": 0.0,
        }
    df = samples.copy().reset_index(drop=True)
    anchors = pd.to_numeric(df["source_row_index"], errors="coerce").fillna(-1).astype(int)
    pre = int(round(window_bars * pre_context_ratio))
    post = max(0, int(window_bars) - pre)

    def _ratio(i: int, j: int) -> float:
        ai, aj = int(anchors.iloc[i]), int(anchors.iloc[j])
        if ai < 0 or aj < 0:
            return 0.0
        w1 = (ai - pre, ai + post)
        w2 = (aj - pre, aj + post)
        lo = max(w1[0], w2[0])
        hi = min(w1[1], w2[1])
        ov = max(0, hi - lo + 1)
        return float(ov / max(1, window_bars))

    groups = []
    max_ratio = 0.0
    first20_max = 0.0
    first30_max = 0.0
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            r = _ratio(i, j)
            max_ratio = max(max_ratio, r)
            if i < 20 and j < 20:
                first20_max = max(first20_max, r)
            if i < 30 and j < 30:
                first30_max = max(first30_max, r)
            if r > overlap_threshold:
                groups.append(
                    {
                        "sample_id_a": str(df.iloc[i].get("sample_id", "")),
                        "sample_id_b": str(df.iloc[j].get("sample_id", "")),
                        "timestamp_a": str(df.iloc[i].get("timestamp", "")),
                        "timestamp_b": str(df.iloc[j].get("timestamp", "")),
                        "candidate_type_a": str(df.iloc[i].get("candidate_type", "")),
                        "candidate_type_b": str(df.iloc[j].get("candidate_type", "")),
                        "overlap_ratio": round(r, 6),
                        "anchor_gap_bars": int(abs(int(anchors.iloc[i]) - int(anchors.iloc[j]))),
                    }
                )
    fallback_count = int(samples.get("fallback_window_overlap", pd.Series([], dtype=bool)).fillna(False).astype(bool).sum())
    return {
        "window_overlap_max_ratio_threshold": float(overlap_threshold),
        "max_window_overlap_ratio": round(float(max_ratio), 6),
        "window_overlap_warning_count": int(len(groups)),
        "window_overlap_duplicate_groups": groups[:40],
        "fallback_window_overlap_count": fallback_count,
        "first20_max_window_overlap": round(float(first20_max), 6),
        "first30_max_window_overlap": round(float(first30_max), 6),
    }


def build_review_batch_report(
    template_csv: Path,
    label_schema_json: Path,
    batch_id: str,
    batch_size: int,
    per_type_target: int,
    output_batch_csv: Path,
    output_batch_jsonl: Path,
    min_gap_bars_between_samples: int = 8,
    max_samples_per_day: int = 8,
    balanced_by_candidate_type: bool = True,
    prefer_time_diversity: bool = True,
    excluded_sample_ids: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Build first review batch from template."""
    if not template_csv.exists():
        return {
            "status": "blocked",
            "reason": "template_csv_missing",
            "recommendation": "generate_review_template"
        }
    
    if not label_schema_json.exists():
        return {
            "status": "blocked",
            "reason": "label_schema_missing",
            "recommendation": "generate_label_schema"
        }
    
    with open(label_schema_json) as f:
        schema = json.load(f)
    
    df = pd.read_csv(template_csv)
    # Enforce trend candidate quality gates at batch selection time.
    if "candidate_type" in df.columns:
        trend_mask = df["candidate_type"].astype(str).str.contains("trend", na=False)
        if "excluded_late_reversal_anchor" in df.columns:
            excluded_mask = df["excluded_late_reversal_anchor"].fillna(False).astype(bool)
            df = df[~(trend_mask & excluded_mask)].copy()
        if "preferred_review_candidate" in df.columns:
            preferred_mask = df["preferred_review_candidate"].fillna(True).astype(bool)
            fallback = df.get("fallback_reason", pd.Series([""] * len(df), index=df.index)).fillna("").astype(str).str.strip()
            df = df[~(trend_mask & (~preferred_mask) & (fallback == ""))].copy()
    excluded_sample_ids = set(excluded_sample_ids or set())
    excluded_present_count = 0
    
    if excluded_sample_ids and "sample_id" in df.columns:
        sid_col = df["sample_id"].astype(str)
        excluded_present_count = int(sid_col.isin(excluded_sample_ids).sum())
        df = df[~sid_col.isin(excluded_sample_ids)].copy()

    # Check forbidden columns
    forbidden_hits = [c for c in df.columns if c.lower() in FORBIDDEN_TRADING_COLUMNS]
    if forbidden_hits:
        return {
            "status": "blocked",
            "reason": "forbidden_trading_columns_detected",
            "forbidden_columns": forbidden_hits,
            "recommendation": "remove_forbidden_columns"
        }
    
    # Select diversified and balanced batch.
    preselected_rows = []
    for ctype in df["candidate_type"].unique():
        ctype_df = df[df["candidate_type"] == ctype].copy()
        ctype_df = ctype_df.sort_values(by=["review_priority", "confidence_score", "timestamp"], ascending=[True, False, True])
        preselected_rows.append(ctype_df.head(per_type_target))
    preselected = pd.concat(preselected_rows, ignore_index=True)
    if len(preselected) < batch_size:
        missing = batch_size - len(preselected)
        rest = df.sort_values(by=["review_priority", "confidence_score", "timestamp"], ascending=[True, False, True]).copy()
        if "sample_id" in preselected.columns and "sample_id" in rest.columns:
            selected_ids = set(preselected["sample_id"].astype(str).tolist())
            rest = rest[~rest["sample_id"].astype(str).isin(selected_ids)]
        preselected = pd.concat([preselected, rest.head(missing)], ignore_index=True)
    preselected = preselected.head(batch_size)
    overlap_cfg = {
        "anchor_duplicate_gap_bars": 8,
        "same_region_cooldown_bars": 48,
        "window_bars": 120,
        "pre_context_ratio": 0.6,
        "window_overlap_max_ratio": 0.35,
    }
    if prefer_time_diversity:
        batch_df = diversify_review_samples(
            preselected,
            target_count=batch_size,
            min_gap_bars=min_gap_bars_between_samples,
            max_samples_per_day=max_samples_per_day,
            balanced_by_candidate_type=balanced_by_candidate_type,
            anchor_duplicate_gap_bars=overlap_cfg["anchor_duplicate_gap_bars"],
            same_region_cooldown_bars=overlap_cfg["same_region_cooldown_bars"],
            window_bars=overlap_cfg["window_bars"],
            pre_context_ratio=overlap_cfg["pre_context_ratio"],
            window_overlap_max_ratio=overlap_cfg["window_overlap_max_ratio"],
        )
    else:
        batch_df = preselected.reset_index(drop=True)
    batch_counts = {
        str(ctype): int((batch_df["candidate_type"] == ctype).sum())
        for ctype in sorted(batch_df["candidate_type"].unique())
    }
    diversity_summary = summarize_sample_time_diversity(batch_df)
    overlap_summary = summarize_window_overlap(
        batch_df,
        window_bars=overlap_cfg["window_bars"],
        pre_context_ratio=overlap_cfg["pre_context_ratio"],
        overlap_threshold=overlap_cfg["window_overlap_max_ratio"],
    )
    
    output_batch_csv.parent.mkdir(parents=True, exist_ok=True)
    batch_df.to_csv(output_batch_csv, index=False)
    
    batch_df.to_json(output_batch_jsonl, orient="records", lines=True)
    
    status = "ready"
    if any(c < per_type_target for c in batch_counts.values()) or diversity_summary.get("status") == "warning" or overlap_summary["window_overlap_warning_count"] > 0:
        status = "watch"
    
    return {
        "status": status,
        "batch_id": batch_id,
        "schema_version": schema.get("schema_version", "unknown"),
        "template_row_count": len(df) + excluded_present_count,
        "template_row_count_after_exclusion": len(df),
        "excluded_sample_count": int(len(excluded_sample_ids)),
        "excluded_sample_count_present_in_template": int(excluded_present_count),
        "batch_row_count": len(batch_df),
        "candidate_type_count": len(batch_counts),
        "batch_count_by_type": batch_counts,
        "selection_policy": f"balanced_{per_type_target}_per_type_up_to_{batch_size}",
        "diversification_settings": {
            "balanced_by_candidate_type": bool(balanced_by_candidate_type),
            "min_gap_bars_between_samples": int(min_gap_bars_between_samples),
            "max_samples_per_day": int(max_samples_per_day),
            "prefer_time_diversity": bool(prefer_time_diversity),
            **overlap_cfg,
        },
        "diversity_summary": diversity_summary,
        "overlap_summary": overlap_summary,
        "output_paths": {
            "batch_csv": str(output_batch_csv),
            "batch_jsonl": str(output_batch_jsonl)
        },
        "forbidden_trading_column_hits": [],
        "recommendation": "review_batch_001"
    }


def format_batch_report_markdown(report: Dict[str, Any]) -> str:
    """Format batch report as markdown."""
    lines = [
        "# EURUSD 15m Pattern Review Batch Report",
        "",
        f"**Status**: `{report['status']}`",
        f"**Batch ID**: `{report['batch_id']}`",
        f"**Schema Version**: `{report['schema_version']}`",
        "",
        "## Batch Summary",
        "",
        f"- Template rows: {report['template_row_count']}",
        f"- Batch rows: {report['batch_row_count']}",
        f"- Candidate types: {report['candidate_type_count']}",
        f"- Selection policy: {report['selection_policy']}",
        "",
        "## Batch Counts by Type",
        ""
    ]
    
    for ctype, count in report["batch_count_by_type"].items():
        lines.append(f"- `{ctype}`: {count}")
    diversity = report.get("diversity_summary", {})
    overlap = report.get("overlap_summary", {})
    settings = report.get("diversification_settings", {})
    lines.extend(
        [
            "",
            "## Diversity",
            "",
            f"- status: `{diversity.get('status')}`",
            f"- unique_days: `{diversity.get('unique_days')}`",
            f"- max_samples_per_day: `{diversity.get('max_samples_per_day')}`",
            f"- min_gap_minutes: `{diversity.get('min_gap_minutes')}`",
            f"- median_gap_minutes: `{diversity.get('median_gap_minutes')}`",
            f"- cluster_warning_count: `{diversity.get('cluster_warning_count')}`",
            f"- min_gap_bars_between_samples: `{settings.get('min_gap_bars_between_samples')}`",
            f"- prefer_time_diversity: `{settings.get('prefer_time_diversity')}`",
            f"- window_overlap_max_ratio_threshold: `{overlap.get('window_overlap_max_ratio_threshold')}`",
            f"- max_window_overlap_ratio: `{overlap.get('max_window_overlap_ratio')}`",
            f"- window_overlap_warning_count: `{overlap.get('window_overlap_warning_count')}`",
            f"- fallback_window_overlap_count: `{overlap.get('fallback_window_overlap_count')}`",
            f"- first20_max_window_overlap: `{overlap.get('first20_max_window_overlap')}`",
            f"- first30_max_window_overlap: `{overlap.get('first30_max_window_overlap')}`",
        ]
    )
    
    lines.extend([
        "",
        "## Output Paths",
        "",
        f"- Batch CSV: `{report['output_paths']['batch_csv']}`",
        f"- Batch JSONL: `{report['output_paths']['batch_jsonl']}`",
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
