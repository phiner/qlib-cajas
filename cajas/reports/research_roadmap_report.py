"""Build phase-55 roadmap report from current research state."""

from __future__ import annotations

import json
from pathlib import Path


def build_research_roadmap_report(*, output_dir: str | Path, run_name: str) -> dict:
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "solid": [
            "external holdout training/evaluation path",
            "label variant and horizon comparison tooling",
            "feature engineering and feature-set comparison scaffold",
        ],
        "weak": [
            "flat class under exact-zero label definition",
            "calibration and seed stability still require larger experiment matrix",
        ],
        "recommended_next_experiments": [
            "threshold-based flat refinement on horizons 4/8/16",
            "binary_drop_flat robustness checks with additional seeds",
            "rolling-year validation execution on selected top configurations",
        ],
        "trading_backtest_discussion_blocked": True,
        "trading_metrics_present": False,
    }
    j = out / "research_roadmap_report.json"
    m = out / "research_roadmap_report.md"
    j.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m.write_text(
        "# Phase 55 Research Roadmap\n\nThis roadmap is classification research only and does not permit trading/backtest conclusions.\n",
        encoding="utf-8",
    )
    report["output_dir"] = str(out)
    return report
