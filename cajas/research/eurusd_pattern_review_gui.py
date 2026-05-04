"""EURUSD 15m pattern review GUI helpers."""
import json
from pathlib import Path
from typing import Any, Dict, Optional

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


def load_clean_view(path: Path) -> pd.DataFrame:
    """Load clean view dataset."""
    return pd.read_csv(path, parse_dates=["timestamp"])


def load_review_batch(path: Path) -> pd.DataFrame:
    """Load review batch."""
    return pd.read_csv(path, parse_dates=["timestamp"])


def load_completed_reviews(path: Path) -> Optional[pd.DataFrame]:
    """Load completed reviews if exists."""
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["timestamp"])


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
    
    return merged


def extract_chart_window(
    clean_view: pd.DataFrame,
    sample_timestamp: pd.Timestamp,
    lookback: int = 60,
    forward: int = 30
) -> pd.DataFrame:
    """Extract chart window around sample timestamp."""
    sample_idx = clean_view[clean_view["timestamp"] == sample_timestamp].index
    if len(sample_idx) == 0:
        return pd.DataFrame()
    
    idx = sample_idx[0]
    start_idx = max(0, idx - lookback)
    end_idx = min(len(clean_view), idx + forward + 1)
    
    return clean_view.iloc[start_idx:end_idx].copy()


def create_candlestick_figure(window_df: pd.DataFrame, sample_timestamp: pd.Timestamp):
    """Create Plotly candlestick figure."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None
    
    fig = go.Figure(data=[go.Candlestick(
        x=window_df["timestamp"],
        open=window_df["open"],
        high=window_df["high"],
        low=window_df["low"],
        close=window_df["close"],
        name="EURUSD"
    )])
    
    # Mark target sample
    sample_row = window_df[window_df["timestamp"] == sample_timestamp]
    if not sample_row.empty:
        fig.add_shape(
            type="line",
            x0=sample_timestamp,
            x1=sample_timestamp,
            y0=float(window_df["low"].min()),
            y1=float(window_df["high"].max()),
            line={"color": "red", "dash": "dash"},
        )
        fig.add_annotation(x=sample_timestamp, y=float(window_df["high"].max()), text="Sample", showarrow=False)
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=500
    )
    
    return fig


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

    completed_df = sanitize_output_columns(completed_df).drop_duplicates(
        subset=["sample_id"], keep="last"
    )

    # Update sample
    mask = completed_df["sample_id"] == sample_id
    if not mask.any():
        batch_row = batch_df.loc[batch_df["sample_id"] == sample_id]
        if not batch_row.empty:
            completed_df = pd.concat([completed_df, batch_row.iloc[[0]]], ignore_index=True)
            completed_df = sanitize_output_columns(completed_df)
            mask = completed_df["sample_id"] == sample_id
    for key, value in labels.items():
        if key in FORBIDDEN_TRADING_COLUMNS:
            continue
        if key not in completed_df.columns:
            completed_df[key] = None
        if key == "review_notes":
            completed_df[key] = completed_df[key].astype("object")
        completed_df.loc[mask, key] = value

    completed_df = sanitize_output_columns(completed_df).drop_duplicates(
        subset=["sample_id"], keep="last"
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_df.to_csv(output_path, index=False)


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
