"""EURUSD 15m Bid research dataset contract report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_INPUT_PATHS = [
    "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv",
    "/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv",
]


def build_validation_eurusd_dataset_contract(
    *,
    input_paths: list[str] | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "15m",
    price_side: str = "Bid",
) -> dict[str, Any]:
    paths = input_paths or list(DEFAULT_INPUT_PATHS)
    fixed_timeframe_ok = timeframe == "15m"
    status = "ready" if fixed_timeframe_ok and symbol == "EURUSD" else "blocked"

    return {
        "schema_version": 1,
        "status": status,
        "symbol": symbol,
        "timeframe": timeframe,
        "price_side": price_side,
        "expected_input_paths": paths,
        "required_columns": {
            "timestamp": "required datetime column (normalized to utc)",
            "open": "required",
            "high": "required",
            "low": "required",
            "close": "required",
        },
        "optional_columns": ["volume", "spread", "source"],
        "column_normalization_aliases": {
            "timestamp": ["time", "time_utc", "timeutc", "datetime", "date", "timestamp", "time_utc_"],
            "open": ["open", "o"],
            "high": ["high", "h"],
            "low": ["low", "l"],
            "close": ["close", "c"],
            "volume": ["volume", "vol", "tickvolume"],
            "spread": ["spread"],
            "source": ["source"],
        },
        "constraints": {
            "high_relation": "high >= max(open, close, low)",
            "low_relation": "low <= min(open, close, high)",
            "duplicate_timestamp_after_normalization": "must be zero",
            "missing_ohlc_rate": "must be reported",
            "large_gaps": "must be reported",
            "timezone_handling": "timestamps are parsed and reported in UTC",
            "price_precision": "decimal precision profile reported from close column",
        },
        "fixed_timeframe_policy": {
            "allowed_timeframe": "15m",
            "aggregation_allowed": False,
            "notes": "No 1H/4H aggregation in this phase.",
        },
        "scope_boundary": {
            "offline_research_only": True,
            "qlib_core_changes": False,
            "live_or_paper_trading": False,
            "broker_routing": False,
            "order_generation": False,
            "production_model_training": False,
        },
    }


def render_validation_eurusd_dataset_contract_markdown(payload: dict[str, Any]) -> str:
    required = payload.get("required_columns", {})
    optional = payload.get("optional_columns", [])
    lines = [
        "# Validation EURUSD Dataset Contract",
        "",
        f"- status: `{payload.get('status')}`",
        f"- symbol: `{payload.get('symbol')}`",
        f"- timeframe: `{payload.get('timeframe')}`",
        f"- price_side: `{payload.get('price_side')}`",
        "",
        "## Expected Input Paths",
        "",
    ]
    lines.extend(f"- `{p}`" for p in payload.get("expected_input_paths", []))
    lines.extend(
        [
            "",
            "## Required Columns",
            "",
        ]
    )
    lines.extend(f"- `{k}`: {v}" for k, v in required.items())
    lines.extend(
        [
            "",
            "## Optional Columns",
            "",
        ]
    )
    lines.extend(f"- `{x}`" for x in optional)
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Research timeframe is fixed to `15m` (Bid side for EURUSD).",
            "- No timeframe aggregation is allowed in this phase.",
            "- Offline research only; no trading execution or broker routing.",
            "",
        ]
    )
    return "\n".join(lines)
