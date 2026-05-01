"""Feature grouping helpers for external holdout ablation planning."""

from __future__ import annotations


def classify_feature_groups(feature_columns: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {
        "price_return": [],
        "range_body": [],
        "volatility": [],
        "rolling_stats": [],
        "time_session": [],
        "other": [],
    }
    for col in feature_columns:
        c = col.lower()
        if "return" in c or c in {"open", "high", "low", "close"}:
            groups["price_return"].append(col)
        elif "range" in c or "body" in c or "shadow" in c or "change" in c:
            groups["range_body"].append(col)
        elif "volatility" in c or "std" in c or "atr" in c:
            groups["volatility"].append(col)
        elif "rolling_" in c or "lag_" in c or "window" in c:
            groups["rolling_stats"].append(col)
        elif "hour" in c or "session" in c or "weekday" in c or "dayofweek" in c:
            groups["time_session"].append(col)
        else:
            groups["other"].append(col)
    return groups


def build_feature_group_audit(feature_columns: list[str]) -> dict:
    groups = classify_feature_groups(feature_columns)
    group_counts = {k: len(v) for k, v in groups.items()}
    return {
        "feature_count": len(feature_columns),
        "group_counts": group_counts,
        "groups": groups,
        "trading_metrics_present": False,
    }
