"""Export compact dashboard-ready JSON/CSV artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd

from cajas.baseline.baseline_run_comparison import compare_baseline_runs
from cajas.baseline.feature_importance_summary import summarize_feature_importance_across_runs
from cajas.registry.registry_reports import build_run_registry_summary
from cajas.registry.run_health_check import check_run_registry_health


@dataclass(frozen=True)
class DashboardExportReport:
    output_dir: str
    run_count: int
    files_written: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def export_dashboard_data(
    *,
    registry_path: str | Path,
    output_dir: str | Path,
    run_name: str,
    baseline_run_dirs: list[str | Path] | None = None,
) -> DashboardExportReport:
    out_dir = Path(output_dir).expanduser().resolve() / run_name
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    warnings: list[str] = []
    files: list[str] = []

    reg_sum = build_run_registry_summary(registry_path=registry_path)
    health = check_run_registry_health(registry_path=registry_path)

    run_rows = reg_sum.training_runs
    pd.DataFrame(run_rows).to_csv(out_dir / "dashboard_runs.csv", index=False)
    (out_dir / "dashboard_runs.json").write_text(json.dumps(run_rows, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files.extend(["dashboard_runs.csv", "dashboard_runs.json"])

    if baseline_run_dirs:
        comp = compare_baseline_runs(run_dirs=baseline_run_dirs)
        pd.DataFrame(comp.rows).to_csv(out_dir / "dashboard_metrics.csv", index=False)
        fi = summarize_feature_importance_across_runs(run_dirs=baseline_run_dirs, top_k=50)
        pd.DataFrame([x.to_dict() for x in fi.features]).to_csv(out_dir / "dashboard_feature_importance.csv", index=False)
        files.extend(["dashboard_metrics.csv", "dashboard_feature_importance.csv"])
        warnings.extend(comp.warnings + fi.warnings)
    else:
        warnings.append("No baseline_run_dirs provided; metrics/feature summaries skipped.")

    health_payload = health.to_dict()
    (out_dir / "dashboard_health_summary.json").write_text(json.dumps(health_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files.append("dashboard_health_summary.json")

    manifest = {
        "registry_path": str(Path(registry_path).expanduser().resolve()),
        "run_count": len(run_rows),
        "files_written": files,
        "warnings": list(dict.fromkeys(warnings)),
    }
    (out_dir / "dashboard_manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files.append("dashboard_manifest.json")

    return DashboardExportReport(
        output_dir=str(out_dir),
        run_count=len(run_rows),
        files_written=files,
        warnings=list(dict.fromkeys(warnings)),
    )
