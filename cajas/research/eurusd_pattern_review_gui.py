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


def extract_chart_window_with_diagnostics(
    clean_view: pd.DataFrame,
    sample_timestamp: Any,
    lookback: int = 60,
    forward: int = 30,
    nearest_tolerance: str = "15min",
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

    start_idx = max(0, idx - lookback)
    end_idx = min(len(df), idx + forward + 1)
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
    )
    return window


def create_candlestick_figure(
    window_df: pd.DataFrame,
    sample_timestamp: Any,
    sample_id: Optional[str] = None,
    candidate_type: Optional[str] = None,
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

    fig = go.Figure(data=[go.Candlestick(
        x=window["timestamp"],
        open=window["open"],
        high=window["high"],
        low=window["low"],
        close=window["close"],
        name="EURUSD"
    )])

    # Mark target sample
    sample_row = window[window["timestamp"] == target_ts]
    if not sample_row.empty:
        fig.add_shape(
            type="line",
            x0=target_ts,
            x1=target_ts,
            y0=float(window["low"].min()),
            y1=float(window["high"].max()),
            line={"color": "#ff5a36", "dash": "dash", "width": 2},
        )
        fig.add_annotation(x=target_ts, y=float(window["high"].max()), text="Sample", showarrow=False)

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
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600,
        template="plotly_dark",
        plot_bgcolor="#0f1720",
        paper_bgcolor="#0f1720",
        font={"color": "#e5edf7"},
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.25)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.25)")
    fig.update_traces(
        increasing_line_color="#00d084",
        increasing_fillcolor="#00d084",
        decreasing_line_color="#ff5a36",
        decreasing_fillcolor="#ff5a36",
    )

    return fig


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
