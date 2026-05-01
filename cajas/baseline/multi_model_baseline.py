"""Run controlled local baselines across multiple model families."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd

from cajas.baseline.local_baseline_trainer import train_local_baseline


@dataclass(frozen=True)
class MultiModelBaselineReport:
    config_path: str
    output_dir: str
    run_name: str
    model_families_requested: list[str]
    model_runs: list[dict]
    comparison: dict
    best_model_by_primary_metric: str | None
    primary_metric: str
    training_executed: bool
    qlib_workflow_executed: bool
    trading_metrics_present: bool
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _slug(name: str) -> str:
    return "_".join(name.lower().replace("-", "_").split())


def run_multi_model_baseline(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    model_families: list[str],
    primary_metric: str = "test_macro_f1",
    input_override: str | None = None,
    random_state: int = 42,
) -> MultiModelBaselineReport:
    out_root = Path(output_dir).expanduser().resolve()
    base_dir = out_root / run_name
    if base_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {base_dir}")
    base_dir.mkdir(parents=True, exist_ok=False)

    warnings: list[str] = []
    blockers: list[str] = []
    model_runs: list[dict] = []
    model_status_rows: list[dict] = []

    supported = {"lightgbm", "randomforest", "histgradientboosting", "random_forest", "hist_gradient_boosting"}

    for family in model_families:
        key = family.lower().replace(" ", "")
        key = key.replace("_", "")
        if key not in supported:
            warnings.append(f"Unsupported model family skipped: {family}")
            model_status_rows.append({"model_family": family, "status": "skipped", "error": "unsupported_model_family", "run_name": ""})
            continue
        sub_name = f"{run_name}_{_slug(family)}"
        try:
            report = train_local_baseline(
                config_path=config_path,
                output_dir=base_dir,
                run_name=sub_name,
                input_override=input_override,
                model_family=family,
                random_state=random_state,
            )
            payload = report.to_dict()
            metric_map = {
                "test_macro_f1": float(payload["metrics"]["test"].get("macro_f1", 0.0)),
                "test_accuracy": float(payload["metrics"]["test"].get("accuracy", 0.0)),
                "test_weighted_f1": float(payload["metrics"]["test"].get("weighted_f1", 0.0)),
                "valid_macro_f1": float(payload["metrics"]["valid"].get("macro_f1", 0.0)),
            }
            model_runs.append(
                {
                    "run_name": sub_name,
                    "run_dir": payload["output_dir"],
                    "model_family_requested": payload["model_family_requested"],
                    "model_family_used": payload["model_family_used"],
                    "metrics": metric_map,
                }
            )
            model_status_rows.append({"model_family": family, "status": "completed", "error": "", "run_name": sub_name})
        except Exception as exc:  # noqa: BLE001
            err = f"{exc}"
            warnings.append(f"Model family {family} failed: {err}")
            model_status_rows.append({"model_family": family, "status": "failed", "error": err, "run_name": sub_name})

    best = None
    if model_runs:
        model_runs.sort(key=lambda x: float(x.get("metrics", {}).get(primary_metric, 0.0)), reverse=True)
        best = model_runs[0]["run_name"]

    summary = {
        "primary_metric": primary_metric,
        "rows": model_runs,
        "best_model": best,
        "model_status": model_status_rows,
    }
    (base_dir / "comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (base_dir / "multi_model_baseline_report.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(model_runs).to_csv(base_dir / "multi_model_metrics.csv", index=False)
    pd.DataFrame(model_status_rows).to_csv(base_dir / "model_run_status.csv", index=False)

    if not model_runs:
        raise RuntimeError("No model completed successfully in multi-model baseline run.")

    return MultiModelBaselineReport(
        config_path=config_path,
        output_dir=str(base_dir),
        run_name=run_name,
        model_families_requested=model_families,
        model_runs=model_runs,
        comparison=summary,
        best_model_by_primary_metric=best,
        primary_metric=primary_metric,
        training_executed=bool(model_runs),
        qlib_workflow_executed=False,
        trading_metrics_present=False,
        warnings=warnings,
        blockers=blockers,
    )
