"""Build classification-research readiness report for future controlled Qlib integration."""

from __future__ import annotations

import json
from pathlib import Path


def build_qlib_readiness_report(*, output_dir: str | Path, run_name: str) -> dict:
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "scope": "classification_research_only",
        "data_readiness": "prepared_datasets_available",
        "label_readiness": "variant_experiments_available",
        "feature_readiness": "feature_set_registry_available",
        "model_baseline_readiness": "external_holdout_baselines_available",
        "artifact_report_readiness": "phase35_to_phase55_reports_available",
        "unresolved_blockers": [
            "flat-class robustness remains weak",
            "no qlib workflow execution approved in current phase",
        ],
        "recommended_integration_path": "keep qlib core untouched; enable controlled workflow only after label/feature stability",
        "qlib_initialized": False,
        "qlib_workflow_executed": False,
        "trading_metrics_present": False,
    }
    j = out / "qlib_readiness_report.json"
    m = out / "qlib_readiness_report.md"
    j.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m.write_text(
        "# Phase 54 Qlib Readiness Report\n\nClassification research only.\n\n- Qlib initialized: false\n- Qlib workflow executed: false\n",
        encoding="utf-8",
    )
    report["output_dir"] = str(out)
    return report
