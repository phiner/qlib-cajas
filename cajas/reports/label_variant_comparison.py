"""Compare label-variant holdout runs by classification metrics."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _parse_horizon_threshold(label_col: str) -> tuple[int | None, float | None]:
    parts = label_col.split("_thr_")
    if len(parts) != 2:
        return None, None
    try:
        h = int(parts[0].split("_")[-1])
    except Exception:
        h = None
    try:
        t = float(parts[1].replace("_", ".").replace("m", "-"))
    except Exception:
        t = None
    return h, t


def compare_label_variant_runs(
    *,
    run_dirs: list[str | Path],
    primary_metric: str = "macro_f1",
) -> dict:
    rows: list[dict] = []
    warnings: list[str] = []
    for run_dir in run_dirs:
        base = Path(run_dir).expanduser().resolve()
        try:
            metrics = json.loads((base / "metrics_holdout.json").read_text(encoding="utf-8"))
            meta = json.loads((base / "model_metadata.json").read_text(encoding="utf-8"))
            dtrain = json.loads((base / "label_distribution_train.json").read_text(encoding="utf-8"))
            dhold = json.loads((base / "label_distribution_holdout.json").read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Skipping {base}: {exc}")
            continue
        label_col = str(meta.get("label_col", ""))
        horizon, threshold = _parse_horizon_threshold(label_col)
        holdout_total = max(sum(dhold.values()), 1)
        rows.append(
            {
                "run_name": base.name,
                "run_dir": str(base),
                "label_col": label_col,
                "label_mode": meta.get("label_mode"),
                "horizon": horizon,
                "threshold": threshold,
                "accuracy": float(metrics.get("accuracy", 0.0)),
                "macro_f1": float(metrics.get("macro_f1", 0.0)),
                "weighted_f1": float(metrics.get("weighted_f1", 0.0)),
                "flat_ratio_holdout": float(dhold.get("flat", 0)) / holdout_total,
                "label_distribution_train": dtrain,
                "label_distribution_holdout": dhold,
            }
        )
    rows.sort(key=lambda x: float(x.get(primary_metric, 0.0)), reverse=True)
    return {
        "run_count": len(rows),
        "primary_metric": primary_metric,
        "best_run": rows[0]["run_name"] if rows else None,
        "rows": rows,
        "warnings": warnings,
        "trading_metrics_present": False,
    }


def write_label_variant_comparison_artifacts(*, report: dict, output_dir: str | Path) -> list[str]:
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    j = out / "label_variant_comparison_report.json"
    c = out / "label_variant_comparison.csv"
    j.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(report["rows"]).to_csv(c, index=False)
    return [str(j), str(c)]
