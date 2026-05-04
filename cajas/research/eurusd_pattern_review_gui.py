"""EURUSD 15m pattern review GUI helpers."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
]
REVIEW_FIELDS = [
    "human_pattern_label",
    "market_context",
    "direction_context",
    "structure_quality",
    "follow_through_quality",
    "review_confidence",
    "review_notes",
    "review_status",
]
OPTIONAL_TEXT_FIELDS = [
    "review_notes",
]
DEFAULT_REVIEW_VALUES = {
    "human_pattern_label": "unclear",
    "market_context": "unclear",
    "direction_context": "unclear",
    "structure_quality": 3,
    "follow_through_quality": 3,
    "review_confidence": 3,
    "review_notes": "",
    "review_status": "pending",
}
REVIEW_SCHEMA_VERSION = "eurusd_15m_pattern_review_v1"
REVIEW_UPDATED_AT_COLUMN = "review_updated_at_utc"
WICK_SENSITIVE_CANDIDATE_TYPES = {
    "lower_wick_rejection_candidate",
    "upper_wick_rejection_candidate",
}


def load_clean_view(path: Path) -> pd.DataFrame:
    """Load clean view dataset."""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if "timestamp" in df.columns:
        df["timestamp"] = normalize_timestamp_series(df["timestamp"])
    return df


def load_review_batch(path: Path) -> pd.DataFrame:
    """Load review batch."""
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if "timestamp" in df.columns:
        df["timestamp"] = normalize_timestamp_series(df["timestamp"])
    return sanitize_optional_text_fields(df)


def load_completed_reviews(path: Path) -> Optional[pd.DataFrame]:
    """Load completed reviews if exists."""
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if "timestamp" in df.columns:
        df["timestamp"] = normalize_timestamp_series(df["timestamp"])
    return sanitize_optional_text_fields(df)


def load_label_schema(path: Path) -> Dict[str, Any]:
    """Load label schema."""
    if not path.exists():
        return get_default_schema()
    with open(path) as f:
        return json.load(f)


def get_default_schema() -> Dict[str, Any]:
    """Get default label schema."""
    return {
        "schema_version": "eurusd_15m_pattern_review_v1",
        "allowed_values": {
            "human_pattern_label": ["valid_pattern", "weak_pattern", "false_positive", "unclear", "skip_bad_context"],
            "market_context": ["trend", "range", "transition", "high_volatility", "low_volatility", "unclear"],
            "direction_context": ["up", "down", "sideways", "mixed", "unclear"],
            "review_status": ["pending", "reviewed"]
        }
    }


def merge_completed_labels(batch_df: pd.DataFrame, completed_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Merge completed labels into batch by sample_id."""
    if completed_df is None:
        return batch_df.copy()
    
    merged = batch_df.copy()
    completed_sanitized = sanitize_output_columns(completed_df).drop_duplicates(
        subset=["sample_id"], keep="last"
    )
    for _, row in completed_sanitized.iterrows():
        sample_id = row["sample_id"]
        mask = merged["sample_id"] == sample_id
        if mask.any():
            for col in REVIEW_FIELDS:
                if col in row:
                    merged.loc[mask, col] = row[col]
    
    return sanitize_optional_text_fields(merged)


def normalize_timestamp_series(series: pd.Series) -> pd.Series:
    """Normalize timestamps to UTC-aware datetime for matching."""
    return pd.to_datetime(series, utc=True, errors="coerce")


def normalize_timestamp_value(value: Any) -> pd.Timestamp:
    """Normalize a timestamp-like value to UTC-aware pandas timestamp."""
    return pd.to_datetime(value, utc=True, errors="coerce")


def sanitize_optional_text_value(value: Any) -> str:
    """Convert NaN/None-like text values to empty string."""
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    if text.strip().lower() == "nan":
        return ""
    return text


def sanitize_optional_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize optional text columns that might contain NaN text."""
    out = df.copy()
    for field in OPTIONAL_TEXT_FIELDS:
        if field in out.columns:
            out[field] = out[field].map(sanitize_optional_text_value)
    return out


def compute_sample_window_bounds(
    target_index: int,
    total_rows: int,
    window_bars: int,
    pre_context_ratio: float = 0.6,
) -> Tuple[int, int]:
    """Compute stable chart window bounds with configurable pre-context."""
    if total_rows <= 0:
        return (0, 0)
    bars = max(1, int(window_bars))
    bars = min(bars, int(total_rows))
    pre_ratio = float(min(max(pre_context_ratio, 0.0), 1.0))
    target = max(0, min(int(target_index), int(total_rows) - 1))
    pre_bars = int(round((bars - 1) * pre_ratio))
    pre_bars = max(0, min(pre_bars, bars - 1))
    start = target - pre_bars
    end = start + bars
    if start < 0:
        end += -start
        start = 0
    if end > total_rows:
        start -= (end - total_rows)
        end = total_rows
        if start < 0:
            start = 0
    return (int(start), int(end))


def extract_chart_window_with_diagnostics(
    clean_view: pd.DataFrame,
    sample_timestamp: Any,
    lookback: int = 60,
    forward: int = 30,
    nearest_tolerance: str = "15min",
    pre_context_ratio: float = 0.6,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Extract chart window around sample timestamp with diagnostics."""
    diagnostics: Dict[str, Any] = {
        "selected_timestamp": str(sample_timestamp),
        "normalized_timestamp": None,
        "exact_timestamp_match_found": False,
        "nearest_fallback_used": False,
        "chart_window_row_count": 0,
        "target_index_in_window": None,
        "target_timestamp_used": None,
        "target_index_global": None,
        "error": None,
    }

    if "timestamp" not in clean_view.columns or clean_view.empty:
        diagnostics["error"] = "clean_view_missing_timestamp_or_empty"
        return pd.DataFrame(), diagnostics

    df = clean_view.copy()
    df["timestamp"] = normalize_timestamp_series(df["timestamp"])
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    target_ts = normalize_timestamp_value(sample_timestamp)
    diagnostics["normalized_timestamp"] = str(target_ts)
    if pd.isna(target_ts):
        diagnostics["error"] = "invalid_sample_timestamp"
        return pd.DataFrame(), diagnostics

    exact_matches = df.index[df["timestamp"] == target_ts].tolist()
    idx: Optional[int] = None
    if exact_matches:
        idx = int(exact_matches[0])
        diagnostics["exact_timestamp_match_found"] = True
    else:
        deltas = (df["timestamp"] - target_ts).abs()
        nearest_idx = int(deltas.idxmin())
        tolerance = pd.Timedelta(nearest_tolerance)
        if pd.notna(deltas.loc[nearest_idx]) and deltas.loc[nearest_idx] <= tolerance:
            idx = nearest_idx
            diagnostics["nearest_fallback_used"] = True

    if idx is None:
        diagnostics["error"] = "timestamp_not_found_within_tolerance"
        return pd.DataFrame(), diagnostics

    window_bars = int(max(1, lookback + forward + 1))
    start_idx, end_idx = compute_sample_window_bounds(
        target_index=idx,
        total_rows=len(df),
        window_bars=window_bars,
        pre_context_ratio=pre_context_ratio,
    )
    window = df.iloc[start_idx:end_idx].copy()
    target_index_in_window = idx - start_idx
    diagnostics["target_index_global"] = idx
    diagnostics["target_index_in_window"] = int(target_index_in_window)
    diagnostics["chart_window_row_count"] = int(len(window))
    diagnostics["target_timestamp_used"] = str(df.iloc[idx]["timestamp"])

    return window, diagnostics


def extract_chart_window(
    clean_view: pd.DataFrame,
    sample_timestamp: pd.Timestamp,
    lookback: int = 60,
    forward: int = 30
) -> pd.DataFrame:
    """Backwards-compatible chart window extraction."""
    window, _ = extract_chart_window_with_diagnostics(
        clean_view,
        sample_timestamp,
        lookback=lookback,
        forward=forward,
        pre_context_ratio=0.6,
    )
    return window


def format_compact_tick_label(ts: Any) -> str:
    """Format timestamp for compact horizontal x-axis labels."""
    normalized = normalize_timestamp_value(ts)
    if pd.isna(normalized):
        return str(ts)
    return normalized.strftime("%m-%d %H:%M")


def build_sample_marker_config(candidate_type: Optional[str]) -> Dict[str, Any]:
    """Build marker style config based on candidate type readability needs."""
    ctype = str(candidate_type or "")
    if ctype in WICK_SENSITIVE_CANDIDATE_TYPES:
        return {
            "mode": "annotation_only",
            "offset_x": 0.0,
            "color": "#ff8c42",
            "label": "Sample",
            "show_symbol": True,
        }
    return {
        "mode": "offset_line_with_arrow",
        "offset_x": 0.35,
        "color": "#ff8c42",
        "label": "Sample",
        "show_symbol": True,
    }


def compute_sample_marker_y(
    sample_high: float,
    visible_high: float,
    visible_low: float,
    offset_ratio: float = 0.04,
) -> float:
    """Compute marker y above sample high while keeping it visible."""
    low = float(min(visible_low, visible_high))
    high = float(max(visible_low, visible_high))
    span = max(high - low, 1e-9)
    candidate = float(sample_high) + (span * float(offset_ratio))
    ceiling = high + (span * 0.12)
    floor = low + (span * 0.15)
    return float(min(max(candidate, floor), ceiling))


def create_candlestick_figure(
    window_df: pd.DataFrame,
    sample_timestamp: Any,
    sample_id: Optional[str] = None,
    candidate_type: Optional[str] = None,
    axis_info: Optional[Dict[str, Any]] = None,
):
    """Create Plotly candlestick figure."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    if window_df.empty:
        return None

    target_ts = normalize_timestamp_value(sample_timestamp)
    window = window_df.copy()
    window["timestamp"] = normalize_timestamp_series(window["timestamp"])
    if axis_info is None:
        axis_info = build_compressed_gap_axis(window["timestamp"].tolist())
    display_x = axis_info.get("display_x", list(range(len(window))))
    custom_timestamps = [str(ts) for ts in window["timestamp"]]

    fig = go.Figure(data=[go.Candlestick(
        x=display_x,
        open=window["open"],
        high=window["high"],
        low=window["low"],
        close=window["close"],
        name="EURUSD",
        customdata=custom_timestamps,
        hovertemplate=(
            "timestamp=%{customdata}<br>"
            "open=%{open}<br>"
            "high=%{high}<br>"
            "low=%{low}<br>"
            "close=%{close}<extra></extra>"
        ),
    )])

    # Mark target sample
    sample_row = window[window["timestamp"] == target_ts]
    if not sample_row.empty:
        sample_idx = int(sample_row.index[0]) - int(window.index[0])
        sample_x = display_x[sample_idx]
        y_min = float(window["low"].min())
        y_max = float(window["high"].max())
        y_span = max(y_max - y_min, 1e-9)
        marker_cfg = build_sample_marker_config(candidate_type)
        mode = marker_cfg["mode"]
        marker_color = marker_cfg["color"]
        label_text = str(marker_cfg.get("label", "Sample"))
        sample_high = float(sample_row["high"].iloc[0]) if "high" in sample_row.columns else y_max
        marker_y = compute_sample_marker_y(sample_high, y_max, y_min, offset_ratio=0.04)
        annotation_top_y = y_max + (0.09 * y_span)
        marker_x_base = float(sample_x)
        if mode == "offset_line_with_arrow":
            marker_x = float(sample_x) + float(marker_cfg.get("offset_x", 0.35))
            fig.add_shape(
                type="line",
                x0=marker_x,
                x1=marker_x,
                y0=y_min,
                y1=y_max,
                line={"color": marker_color, "dash": "dash", "width": 1.4},
            )
            fig.add_annotation(
                x=marker_x_base,
                y=marker_y,
                ax=marker_x,
                ay=annotation_top_y,
                text=label_text,
                showarrow=True,
                arrowhead=2,
                arrowsize=0.9,
                arrowwidth=1.2,
                arrowcolor=marker_color,
                font={"size": 10, "color": marker_color},
            )
        else:
            fig.add_annotation(
                x=marker_x_base,
                y=marker_y,
                ax=marker_x_base + 0.45,
                ay=annotation_top_y,
                text=label_text,
                showarrow=True,
                arrowhead=2,
                arrowsize=0.9,
                arrowwidth=1.2,
                arrowcolor=marker_color,
                font={"size": 10, "color": marker_color},
            )
        if bool(marker_cfg.get("show_symbol", True)):
            fig.add_trace(
                go.Scatter(
                    x=[marker_x_base],
                    y=[marker_y],
                    mode="markers",
                    marker={
                        "symbol": "diamond-open",
                        "size": 10,
                        "color": marker_color,
                        "line": {"color": marker_color, "width": 1.5},
                    },
                    name="Sample marker",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    for gap in axis_info.get("gap_markers", []):
        gx = gap.get("display_x")
        if gx is None:
            continue
        fig.add_shape(
            type="line",
            x0=gx,
            x1=gx,
            y0=float(window["low"].min()),
            y1=float(window["high"].max()),
            line={"color": "#fbbf24", "dash": "dot", "width": 1},
        )
        label = str(gap.get("label", "Large time gap"))
        fig.add_annotation(
            x=gx,
            y=float(window["high"].max()),
            text=label,
            showarrow=False,
            font={"size": 10, "color": "#fbbf24"},
        )

    title_parts = []
    if sample_id:
        title_parts.append(f"sample_id={sample_id}")
    if not pd.isna(target_ts):
        title_parts.append(f"timestamp={target_ts}")
    if candidate_type:
        title_parts.append(f"candidate_type={candidate_type}")
    title_text = " | ".join(title_parts) if title_parts else "EURUSD Candlestick Window"

    fig.update_layout(
        title=title_text,
        xaxis_title="Compressed candle axis",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        plot_bgcolor="#0f1720",
        paper_bgcolor="#0f1720",
        font={"color": "#e5edf7"},
        margin={"l": 30, "r": 18, "t": 68, "b": 28},
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148, 163, 184, 0.25)",
        tickangle=0,
        ticks="outside",
        tickfont={"size": 10},
        automargin=True,
    )
    tickvals = axis_info.get("tickvals", [])
    ticktext = axis_info.get("ticktext", [])
    if tickvals and ticktext:
        fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.25)")
    padding = max((float(window["high"].max()) - float(window["low"].min())) * 0.14, 1e-9)
    fig.update_yaxes(range=[float(window["low"].min()) - (padding * 0.03), float(window["high"].max()) + padding])
    fig.update_traces(
        increasing_line_color="#00d084",
        increasing_fillcolor="#00d084",
        decreasing_line_color="#ff5a36",
        decreasing_fillcolor="#ff5a36",
        selector={"type": "candlestick"},
    )

    return fig


def detect_time_axis_gaps(
    timestamps: list[Any],
    expected_interval_minutes: int = 15,
    gap_threshold_bars: int = 4,
) -> list[Dict[str, Any]]:
    """Detect large time gaps between consecutive bars."""
    normalized = [normalize_timestamp_value(ts) for ts in timestamps]
    gaps: list[Dict[str, Any]] = []
    threshold_minutes = expected_interval_minutes * gap_threshold_bars
    for i in range(len(normalized) - 1):
        prev_ts = normalized[i]
        next_ts = normalized[i + 1]
        if pd.isna(prev_ts) or pd.isna(next_ts):
            continue
        delta = next_ts - prev_ts
        gap_minutes = float(delta.total_seconds() / 60.0)
        if gap_minutes <= threshold_minutes:
            continue
        prev_weekday = int(prev_ts.weekday())
        next_weekday = int(next_ts.weekday())
        is_weekend_gap = prev_weekday == 4 and next_weekday in {6, 0} and gap_minutes >= 24 * 60
        if is_weekend_gap:
            classification = "weekend_or_market_closed_gap"
            label = "Weekend / market closed"
        elif gap_minutes >= 24 * 60:
            classification = "holiday_or_market_closed_gap"
            label = "Holiday / market closed"
        else:
            classification = "missing_bars_or_data_gap"
            label = "Large time gap"
        gaps.append(
            {
                "prev_index": i,
                "next_index": i + 1,
                "start_timestamp": str(prev_ts),
                "end_timestamp": str(next_ts),
                "gap_minutes": gap_minutes,
                "gap_hours": gap_minutes / 60.0,
                "classification": classification,
                "label": label,
                "display_label": (
                    f"{label}\n{str(prev_ts)} -> {str(next_ts)}\n{gap_minutes/60.0:.1f}h gap compressed"
                ),
            }
        )
    return gaps


def build_compressed_gap_axis(timestamps: list[Any]) -> Dict[str, Any]:
    """Build compressed display axis metadata from timestamps."""
    normalized = [normalize_timestamp_value(ts) for ts in timestamps]
    display_x = list(range(len(normalized)))
    gaps = detect_time_axis_gaps(timestamps)
    tickvals: list[int] = []
    ticktext: list[str] = []
    if normalized:
        step = max(1, len(normalized) // 8)
        for i in range(0, len(normalized), step):
            tickvals.append(i)
            ticktext.append(format_compact_tick_label(normalized[i]))
        if tickvals[-1] != len(normalized) - 1:
            tickvals.append(len(normalized) - 1)
            ticktext.append(format_compact_tick_label(normalized[-1]))
    gap_markers = []
    for g in gaps:
        marker = dict(g)
        marker["display_x"] = g["prev_index"] + 0.5
        gap_markers.append(marker)
    return {
        "display_axis": "compressed_gap_axis" if gaps else "real_time_axis",
        "raw_time_axis_preserved_in_hover": True,
        "display_x": display_x,
        "tickvals": tickvals,
        "ticktext": ticktext,
        "gaps": gaps,
        "gap_markers": gap_markers,
    }


def summarize_compressed_gap_axis(axis_info: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize compressed gap axis diagnostics."""
    gaps = axis_info.get("gaps", [])
    largest_gap_hours = max([float(g.get("gap_hours", 0.0)) for g in gaps], default=0.0)
    return {
        "display_axis": axis_info.get("display_axis", "real_time_axis"),
        "raw_time_axis_preserved_in_hover": bool(axis_info.get("raw_time_axis_preserved_in_hover", True)),
        "time_gap_count": len(gaps),
        "largest_gap_hours": largest_gap_hours,
        "gap_markers": len(axis_info.get("gap_markers", [])),
        "gaps": axis_info.get("gap_markers", []),
    }


def build_chart_diagnostic_summary(diagnostics: Dict[str, Any], trace_count: int) -> str:
    """Build a compact always-visible diagnostic summary for chart rendering."""
    return (
        f"Chart window: {int(diagnostics.get('chart_window_row_count', 0))} rows"
        f" | traces: {int(trace_count)}"
        f" | exact match: {bool(diagnostics.get('exact_timestamp_match_found', False))}"
        f" | fallback: {bool(diagnostics.get('nearest_fallback_used', False))}"
        f" | target index: {diagnostics.get('target_index_in_window')}"
    )


def get_chart_height(compact_mode: bool, compact_height: int) -> int:
    """Return chart height for compact and normal modes."""
    return int(compact_height) if compact_mode else 600


def build_compact_chart_diagnostic_summary(diagnostics: Dict[str, Any], trace_count: int) -> str:
    """Build concise one-line diagnostics for compact mode."""
    exact = "✓" if bool(diagnostics.get("exact_timestamp_match_found", False)) else "✗"
    fallback = "✓" if bool(diagnostics.get("nearest_fallback_used", False)) else "✗"
    return (
        f"Window {int(diagnostics.get('chart_window_row_count', 0))} bars"
        f" | traces {int(trace_count)}"
        f" | exact match {exact}"
        f" | fallback {fallback}"
        f" | target index {diagnostics.get('target_index_in_window')}"
    )


def save_completed_review(
    batch_df: pd.DataFrame,
    sample_id: str,
    labels: Dict[str, Any],
    output_path: Path
) -> None:
    """Save or update completed review."""
    # Load existing or start from batch
    if output_path.exists():
        completed_df = pd.read_csv(output_path, parse_dates=["timestamp"])
    else:
        completed_df = batch_df.copy()

    completed_df = sanitize_optional_text_fields(
        sanitize_output_columns(completed_df)
    ).drop_duplicates(
        subset=["sample_id"], keep="last"
    )

    # Update sample
    mask = completed_df["sample_id"] == sample_id
    batch_row = batch_df.loc[batch_df["sample_id"] == sample_id]
    if not mask.any():
        if not batch_row.empty:
            completed_df = pd.concat([completed_df, batch_row.iloc[[0]]], ignore_index=True)
            completed_df = sanitize_optional_text_fields(
                sanitize_output_columns(completed_df)
            )
            mask = completed_df["sample_id"] == sample_id
    if not batch_row.empty:
        identity_values = batch_row.iloc[0].to_dict()
        for key, value in identity_values.items():
            if key in FORBIDDEN_TRADING_COLUMNS:
                continue
            if key not in completed_df.columns:
                completed_df[key] = None
            if key in OPTIONAL_TEXT_FIELDS:
                value = sanitize_optional_text_value(value)
                completed_df[key] = completed_df[key].astype("object")
            completed_df.loc[mask, key] = value
    for key, value in labels.items():
        if key in FORBIDDEN_TRADING_COLUMNS:
            continue
        if key not in completed_df.columns:
            completed_df[key] = None
        if key in OPTIONAL_TEXT_FIELDS:
            value = sanitize_optional_text_value(value)
            completed_df[key] = completed_df[key].astype("object")
        completed_df.loc[mask, key] = value
    if REVIEW_UPDATED_AT_COLUMN not in completed_df.columns:
        completed_df[REVIEW_UPDATED_AT_COLUMN] = None
    completed_df.loc[mask, REVIEW_UPDATED_AT_COLUMN] = datetime.now(timezone.utc).isoformat()

    completed_df = sanitize_optional_text_fields(
        sanitize_output_columns(completed_df)
    ).drop_duplicates(
        subset=["sample_id"], keep="last"
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_df.to_csv(output_path, index=False)


def default_review_values() -> Dict[str, Any]:
    """Return default review values used by reset and new samples."""
    return dict(DEFAULT_REVIEW_VALUES)


def build_review_update_row(overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Build a complete review payload with sanitized optional text fields."""
    row = default_review_values()
    row.update(overrides)
    row["review_notes"] = sanitize_optional_text_value(row.get("review_notes", ""))
    return {key: row[key] for key in REVIEW_FIELDS}


def save_or_update_completed_review(
    batch_df: pd.DataFrame,
    sample_id: str,
    review_values: Dict[str, Any],
    output_path: Path,
) -> Dict[str, Any]:
    """Save or update one sample review by sample_id and return persistence metadata."""
    existing = None
    if output_path.exists():
        existing = pd.read_csv(output_path)
    is_update = bool(existing is not None and "sample_id" in existing.columns and (existing["sample_id"] == sample_id).any())
    labels = build_review_update_row(review_values)
    save_completed_review(batch_df=batch_df, sample_id=sample_id, labels=labels, output_path=output_path)
    return {
        "sample_id": sample_id,
        "action_result": "update" if is_update else "insert",
        "completed_csv_path": str(output_path),
        "review_values": labels,
    }


def append_review_event_jsonl(
    jsonl_path: Path,
    sample_id: str,
    review_values: Dict[str, Any],
    action_type: str,
    completed_csv_path: Path,
    batch_path: Optional[str] = None,
) -> None:
    """Append one review event record to JSONL audit/interchange output."""
    payload = {
        "event_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": REVIEW_SCHEMA_VERSION,
        "action_type": action_type,
        "sample_id": sample_id,
        "completed_csv_path": str(completed_csv_path),
        "source_batch_path": batch_path,
        "review": build_review_update_row(review_values),
    }
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=True) + "\n")


def build_persistence_status_message(
    *,
    sample_id: str,
    action_result: str,
    action_type: str,
    completed_csv_path: str,
    jsonl_path: str,
    jsonl_status: str,
    sample_index: int,
) -> str:
    """Build compact user-visible persistence status text."""
    return (
        f"{action_type}: sample_id={sample_id} ({action_result})"
        f" | csv={completed_csv_path}"
        f" | jsonl={jsonl_path} [{jsonl_status}]"
        f" | sample_index={sample_index}"
    )


def clamp_sample_index(value: int, row_count: int) -> int:
    """Clamp sample index into valid range [0, row_count-1]."""
    if row_count <= 0:
        return 0
    return max(0, min(int(value), int(row_count) - 1))


def next_sample_index(value: int, row_count: int) -> int:
    """Return next sample index without exceeding the last row."""
    return clamp_sample_index(int(value) + 1, row_count)


def previous_sample_index(value: int, row_count: int) -> int:
    """Return previous sample index without going below zero."""
    return clamp_sample_index(int(value) - 1, row_count)


def should_advance_after_save(action_result: Dict[str, Any]) -> bool:
    """Save-and-next advances when CSV save succeeded, even if JSONL warned."""
    return bool(action_result.get("ok")) and bool(action_result.get("csv_saved"))


def build_compact_save_feedback_message(
    *,
    sample_id: str,
    action_type: str,
    moved_to_human_index: Optional[int] = None,
    total_count: Optional[int] = None,
) -> str:
    """Build compact user-facing save feedback without file paths."""
    if action_type == "save_and_next" and moved_to_human_index is not None and total_count is not None:
        return f"Saved {sample_id} -> moved to sample {moved_to_human_index}/{total_count}"
    return f"Saved {sample_id}"


def save_review_action(
    *,
    batch_df: pd.DataFrame,
    sample_id: str,
    review_values: Dict[str, Any],
    completed_csv_path: Path,
    audit_jsonl_path: Path,
    action_type: str,
    source_batch_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist one review action with CSV-first durability and JSONL audit append."""
    result = save_or_update_completed_review(
        batch_df=batch_df,
        sample_id=sample_id,
        review_values=review_values,
        output_path=completed_csv_path,
    )
    out: Dict[str, Any] = {
        "ok": True,
        "sample_id": sample_id,
        "action_type": action_type,
        "action_result": result["action_result"],
        "completed_csv_path": str(completed_csv_path),
        "audit_jsonl_path": str(audit_jsonl_path),
        "csv_saved": True,
        "jsonl_appended": False,
        "warning": None,
        "error": None,
    }
    try:
        append_review_event_jsonl(
            jsonl_path=audit_jsonl_path,
            sample_id=sample_id,
            review_values=review_values,
            action_type=action_type,
            completed_csv_path=completed_csv_path,
            batch_path=source_batch_path,
        )
        out["jsonl_appended"] = True
    except Exception as exc:
        out["warning"] = f"jsonl_append_failed: {exc}"
    return out


def sanitize_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop forbidden trading/action columns from output."""
    drop_cols = [col for col in df.columns if col.lower() in FORBIDDEN_TRADING_COLUMNS]
    if not drop_cols:
        return df.copy()
    return df.drop(columns=drop_cols).copy()


def get_review_progress(batch_df: pd.DataFrame) -> Dict[str, int]:
    """Get review progress summary."""
    total = len(batch_df)
    reviewed = len(batch_df[batch_df["review_status"] == "reviewed"])
    skipped = len(batch_df[batch_df["human_pattern_label"] == "skip_bad_context"])
    pending = total - reviewed
    
    return {
        "total": total,
        "reviewed": reviewed,
        "pending": pending,
        "skipped": skipped
    }
