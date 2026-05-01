"""Build phase-45 label decision report from label-variant comparison artifacts."""

from __future__ import annotations

import json
from pathlib import Path


def build_label_decision_report(
    *,
    comparison_report_path: str | Path,
    output_dir: str | Path,
    run_name: str,
) -> dict:
    comp = json.loads(Path(comparison_report_path).expanduser().resolve().read_text(encoding="utf-8"))
    rows = comp.get("rows", [])
    best = rows[0] if rows else None
    recommendation = "insufficient_data"
    if best is not None:
        mode = str(best.get("label_mode"))
        horizon = best.get("horizon")
        threshold = best.get("threshold")
        recommendation = f"prioritize {mode} on horizon={horizon} threshold={threshold} for next research iteration"

    summary = {
        "scope": "classification_research_only",
        "best_run": best,
        "recommendation": recommendation,
        "forbidden_interpretations": [
            "no buy/sell rules",
            "no trading strategy recommendations",
            "no backtest/profit conclusions",
        ],
        "trading_recommendations_present": False,
    }

    out = Path(output_dir).expanduser().resolve() / run_name
    out.mkdir(parents=True, exist_ok=False)
    j = out / "label_decision_report.json"
    m = out / "label_decision_report.md"
    j.write_text(json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# Phase 45 Label Decision Report",
        "",
        "Scope: classification research only.",
        "",
        "## Recommendation",
        f"- {recommendation}",
        "",
        "## Boundaries",
        "- No trading signal interpretation.",
        "- No backtest/profit conclusions.",
    ]
    m.write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"output_dir": str(out), "files": [str(j), str(m)], **summary}
