"""Run external holdout comparison across feature-set definitions."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.baseline.classification_metrics import compute_classification_metrics
from cajas.baseline.local_baseline_trainer import _make_model
from cajas.baseline.numeric_sanitizer import sanitize_features_for_model
from cajas.features.feature_set_registry import resolve_feature_columns_for_set


def run_feature_set_comparison(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    feature_sets: list[str],
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> dict:
    train_df = pd.read_csv(Path(train_path).expanduser().resolve())
    holdout_df = pd.read_csv(Path(holdout_path).expanduser().resolve())
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)

    rows: list[dict] = []
    warnings: list[str] = []
    for feature_set in feature_sets:
        cols = resolve_feature_columns_for_set(all_columns=train_df.columns.tolist(), feature_set=feature_set, label_col=label_col)
        tr = train_df[train_df[label_col].notna()].copy()
        ho = holdout_df[holdout_df[label_col].notna()].copy()
        ytr = tr[label_col].astype(str)
        yho = ho[label_col].astype(str)
        labels = sorted(set(ytr.unique()).intersection(set(yho.unique())))
        mapping = {n: i for i, n in enumerate(labels)}
        if len(mapping) < 2:
            warnings.append(f"{feature_set}: insufficient class overlap")
            continue
        ytr = ytr.map(mapping)
        yho = yho.map(mapping)
        xtr, _ = sanitize_features_for_model(tr[cols])
        xho, _ = sanitize_features_for_model(ho[cols])
        _, family_used, model = _make_model(model_family, random_state, warnings)
        model.fit(xtr, ytr)
        pred = model.predict(xho)
        metrics = compute_classification_metrics(
            y_true=yho.astype(int),
            y_pred=pred,
            labels=list(range(len(labels))),
            label_names=labels,
        )
        rows.append(
            {
                "feature_set": feature_set,
                "feature_count": len(cols),
                "model_family_used": family_used,
                "accuracy": float(metrics.get("accuracy", 0.0)),
                "macro_f1": float(metrics.get("macro_f1", 0.0)),
                "weighted_f1": float(metrics.get("weighted_f1", 0.0)),
            }
        )

    rows.sort(key=lambda x: x["macro_f1"], reverse=True)
    report = {
        "label_col": label_col,
        "rows": rows,
        "best_feature_set": rows[0]["feature_set"] if rows else None,
        "warnings": warnings,
        "trading_metrics_present": False,
    }
    (out / "feature_set_comparison_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(out / "feature_set_comparison.csv", index=False)
    report["output_dir"] = str(out)
    return report
