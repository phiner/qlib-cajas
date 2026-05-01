"""Run comparison report for qlib model bridge registry."""

from __future__ import annotations


def build_qlib_model_run_comparison(*, records: list[dict]) -> dict:
    ranked = sorted(
        records,
        key=lambda r: (
            float(r.get("metrics", {}).get("macro_f1", -1.0)),
            float(r.get("metrics", {}).get("accuracy", -1.0)),
        ),
        reverse=True,
    )
    return {
        "scope": "research_only",
        "not_trading_decision": True,
        "run_count": len(records),
        "ranked_runs": ranked,
    }
