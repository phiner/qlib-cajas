"""EURUSD 15m pattern review GUI helpers."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


FORBIDDEN_TRADING_COLUMNS = [
    "buy", "sell", "long", "short", "order", "position",
    "target_position", "signal", "entry", "exit"
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
    for idx, row in completed_df.iterrows():
        sample_id = row["sample_id"]
        mask = merged["sample_id"] == sample_id
        if mask.any():
            for col in ["human_pattern_label", "market_context", "direction_context",
                       "structure_quality", "follow_through_quality", "review_confidence",
                       "review_notes", "review_status"]:
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
        fig.add_vline(
            x=sample_timestamp,
            line_dash="dash",
            line_color="red",
            annotation_text="Sample"
        )
    
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
    
    # Update sample
    mask = completed_df["sample_id"] == sample_id
    for key, value in labels.items():
        if key in FORBIDDEN_TRADING_COLUMNS:
            continue
        completed_df.loc[mask, key] = value
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed_df.to_csv(output_path, index=False)


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
