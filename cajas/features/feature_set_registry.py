"""Feature set registry and feature-selection resolution rules."""

from __future__ import annotations


def list_feature_sets() -> dict:
    return {
        "minimal_v1": {"include_keywords": ["return", "range", "body", "shadow", "close", "open", "high", "low", "volume"]},
        "structure_v1": {"include_keywords": ["wick", "location", "ratio", "range", "body", "return", "close", "open", "high", "low"]},
        "structure_plus_rolling_v1": {
            "include_keywords": [
                "wick",
                "location",
                "ratio",
                "range",
                "body",
                "return",
                "rolling_",
                "efficiency_",
                "slope_",
                "atr_like",
                "close",
                "open",
                "high",
                "low",
            ]
        },
    }


def _is_forbidden(col: str, label_col: str) -> bool:
    c = col.lower()
    return c == label_col.lower() or c.startswith("future_close_") or c.startswith("future_return_") or c.startswith("future_direction_")


def resolve_feature_columns_for_set(
    *,
    all_columns: list[str],
    feature_set: str,
    label_col: str,
) -> list[str]:
    sets = list_feature_sets()
    if feature_set not in sets:
        raise ValueError(f"unknown feature set: {feature_set}")
    kws = sets[feature_set]["include_keywords"]
    out: list[str] = []
    for col in all_columns:
        if col in {"datetime", "symbol", "timeframe"}:
            continue
        if _is_forbidden(col, label_col):
            continue
        low = col.lower()
        if any(k in low for k in kws):
            out.append(col)
    return sorted(dict.fromkeys(out))
