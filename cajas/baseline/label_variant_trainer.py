"""Train external holdout models on configurable label variants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import pickle

import pandas as pd

from cajas.baseline.classification_metrics import compute_classification_metrics
from cajas.baseline.local_baseline_trainer import _make_model
from cajas.baseline.numeric_sanitizer import sanitize_features_for_model
from cajas.datasets.label_variant_dataset import LabelVariantExternalHoldoutDataset


@dataclass(frozen=True)
class LabelVariantTrainingReport:
    label_col: str
    label_mode: str
    model_family: str
    train_rows: int
    holdout_rows: int
    feature_count: int
    holdout_metrics: dict
    label_distribution_train: dict
    label_distribution_holdout: dict
    output_dir: str
    artifact_files: list[str]
    warnings: list[str]
    blockers: list[str]
    trading_metrics_present: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def train_label_variant_external_holdout(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    label_col: str,
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    label_mode: str = "multiclass",
    random_state: int = 42,
) -> LabelVariantTrainingReport:
    warnings: list[str] = []
    blockers: list[str] = []
    run_dir = Path(output_dir).expanduser().resolve() / run_name
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    ds = LabelVariantExternalHoldoutDataset(train_path=train_path, holdout_path=holdout_path, label_col=label_col)
    x_train, y_train = ds.prepare_train()
    x_holdout, y_holdout = ds.prepare_holdout()
    if label_mode == "binary_drop_flat":
        keep_train = y_train.isin(["down", "up"])
        keep_holdout = y_holdout.isin(["down", "up"])
        x_train = x_train.loc[keep_train]
        y_train = y_train.loc[keep_train]
        x_holdout = x_holdout.loc[keep_holdout]
        y_holdout = y_holdout.loc[keep_holdout]
        mapping = {"down": 0, "up": 1}
        label_names = ["down", "up"]
    else:
        mapping = {"down": 0, "flat": 1, "up": 2}
        label_names = ["down", "flat", "up"]

    y_train_enc = y_train.map(mapping)
    y_holdout_enc = y_holdout.map(mapping)
    valid_train = y_train_enc.notna()
    valid_holdout = y_holdout_enc.notna()
    x_train, y_train_enc = x_train.loc[valid_train], y_train_enc.loc[valid_train].astype(int)
    x_holdout, y_holdout_enc = x_holdout.loc[valid_holdout], y_holdout_enc.loc[valid_holdout].astype(int)

    x_train_s, _ = sanitize_features_for_model(x_train)
    x_holdout_s, _ = sanitize_features_for_model(x_holdout)
    _, family_used, model = _make_model(model_family, random_state, warnings)
    model.fit(x_train_s, y_train_enc)
    pred = model.predict(x_holdout_s)
    proba = model.predict_proba(x_holdout_s) if hasattr(model, "predict_proba") else None
    labels = [mapping[n] for n in label_names]
    metrics = compute_classification_metrics(y_true=y_holdout_enc, y_pred=pred, labels=labels, label_names=label_names)

    inv_map = {v: k for k, v in mapping.items()}
    pred_df = pd.DataFrame({"label": y_holdout.astype(str).values, "predicted_encoded_label": pred})
    pred_df["predicted_label"] = pd.Series(pred).map(inv_map).fillna("unknown")
    if proba is not None:
        for idx, name in inv_map.items():
            if idx < proba.shape[1]:
                pred_df[f"proba_{name}"] = proba[:, idx]
    pred_df.to_csv(run_dir / "predictions_holdout.csv", index=False)
    pd.DataFrame(metrics["confusion_matrix"]["rows"]).to_csv(run_dir / "confusion_matrix_holdout.csv", index=False)
    _write_json(run_dir / "metrics_holdout.json", metrics)
    _write_json(run_dir / "feature_columns.json", {"feature_columns": ds.feature_columns})
    _write_json(run_dir / "label_distribution_train.json", {k: int(v) for k, v in y_train.value_counts().to_dict().items()})
    _write_json(run_dir / "label_distribution_holdout.json", {k: int(v) for k, v in y_holdout.value_counts().to_dict().items()})
    _write_json(
        run_dir / "model_metadata.json",
        {"label_col": label_col, "label_mode": label_mode, "model_family_requested": model_family, "model_family_used": family_used},
    )
    _write_json(run_dir / "run_manifest.json", {"run_name": run_name, "scope": "label_variant_external_holdout_classification_only"})

    model_path = run_dir / "model.joblib"
    try:
        import joblib

        joblib.dump(model, model_path)
    except Exception:
        with (run_dir / "model.pkl").open("wb") as f:
            pickle.dump(model, f)
        warnings.append("joblib unavailable; wrote pickle model artifact instead")

    artifact_files = sorted(p.name for p in run_dir.glob("*") if p.is_file())
    out = LabelVariantTrainingReport(
        label_col=label_col,
        label_mode=label_mode,
        model_family=family_used,
        train_rows=int(len(y_train)),
        holdout_rows=int(len(y_holdout)),
        feature_count=len(ds.feature_columns),
        holdout_metrics=metrics,
        label_distribution_train={k: int(v) for k, v in y_train.value_counts().to_dict().items()},
        label_distribution_holdout={k: int(v) for k, v in y_holdout.value_counts().to_dict().items()},
        output_dir=str(run_dir),
        artifact_files=artifact_files,
        warnings=warnings,
        blockers=blockers,
        trading_metrics_present=False,
    )
    _write_json(run_dir / "label_variant_training_report.json", out.to_dict())
    return out
