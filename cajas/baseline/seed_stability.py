"""Seed stability runner for label-variant external holdout classification."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from cajas.baseline.label_variant_trainer import train_label_variant_external_holdout


def run_seed_stability_experiment(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    output_dir: str | Path,
    run_name: str,
    seeds: list[int],
    model_family: str = "LightGBM",
) -> dict:
    out = Path(output_dir).expanduser().resolve() / run_name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    rows: list[dict] = []
    for seed in seeds:
        rep = train_label_variant_external_holdout(
            train_path=train_path,
            holdout_path=holdout_path,
            label_col=label_col,
            output_dir=out,
            run_name=f"seed_{seed}",
            model_family=model_family,
            random_state=seed,
            label_mode="multiclass",
        )
        rows.append({"seed": seed, "accuracy": rep.holdout_metrics.get("accuracy", 0.0), "macro_f1": rep.holdout_metrics.get("macro_f1", 0.0)})

    df = pd.DataFrame(rows)
    report = {
        "label_col": label_col,
        "model_family": model_family,
        "seeds": seeds,
        "rows": rows,
        "accuracy_mean": float(df["accuracy"].mean()) if not df.empty else None,
        "accuracy_std": float(df["accuracy"].std(ddof=0)) if not df.empty else None,
        "macro_f1_mean": float(df["macro_f1"].mean()) if not df.empty else None,
        "macro_f1_std": float(df["macro_f1"].std(ddof=0)) if not df.empty else None,
        "trading_metrics_present": False,
    }
    (out / "seed_stability_report.json").write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    df.to_csv(out / "seed_stability_metrics.csv", index=False)
    report["output_dir"] = str(out)
    return report
