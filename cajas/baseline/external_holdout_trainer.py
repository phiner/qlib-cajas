"""Train on multi-year train dataset and evaluate on external 2025 holdout."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import pickle

import pandas as pd

from cajas.baseline.classification_metrics import compute_classification_metrics
from cajas.baseline.feature_value_audit import audit_feature_values
from cajas.baseline.label_encoding import default_future_direction_8_encoding, encode_labels_for_preview
from cajas.baseline.local_baseline_trainer import _make_model
from cajas.baseline.numeric_sanitizer import sanitize_features_for_model
from cajas.datasets.external_holdout_dataset import ExternalHoldoutDataset
from cajas.registry.run_registry import RunRegistryRecord, append_run_registry_record, build_run_id


@dataclass(frozen=True)
class ExternalHoldoutTrainingReport:
    run_name: str
    model_family_requested: str
    model_family_used: str
    target_label: str
    feature_count: int
    train_rows: int
    holdout_rows: int
    train_time_range: dict
    holdout_time_range: dict
    training_executed: bool
    holdout_evaluation_executed: bool
    model_artifact_created: bool
    prediction_artifacts_created: bool
    metrics_artifacts_created: bool
    output_dir: str
    artifact_files: list[str]
    holdout_metrics: dict
    label_distribution_train: dict
    label_distribution_holdout: dict
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_prediction_frame(df: pd.DataFrame, label_col: str, y_true_enc: pd.Series, y_pred_enc, inv_map: dict[int, str], proba) -> pd.DataFrame:
    cols = [c for c in ("datetime", "symbol", "timeframe") if c in df.columns]
    out = df[cols].copy() if cols else pd.DataFrame(index=df.index)
    out["label"] = df[label_col].astype(str).values
    out["encoded_label"] = y_true_enc.astype(int).values
    pred = pd.Series(y_pred_enc, index=df.index).astype(int)
    out["predicted_encoded_label"] = pred.values
    out["predicted_label"] = pred.map(inv_map).fillna("unknown").values
    if proba is not None:
        for idx, name in inv_map.items():
            if idx < proba.shape[1]:
                out[f"proba_{name}"] = proba[:, idx]
    return out


def train_external_holdout_baseline(
    *,
    train_path: str | Path,
    holdout_path: str | Path,
    output_dir: str | Path,
    run_name: str,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> ExternalHoldoutTrainingReport:
    out_root = Path(output_dir).expanduser().resolve()
    run_dir = out_root / run_name
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    warnings: list[str] = []
    blockers: list[str] = []

    dataset = ExternalHoldoutDataset(train_path=train_path, holdout_path=holdout_path)
    summary = dataset.summary()
    train_x, train_y = dataset.prepare_train()
    holdout_x, holdout_y = dataset.prepare_holdout()

    mapping = default_future_direction_8_encoding().mapping
    inv_mapping = {v: k for k, v in mapping.items()}
    labels = [mapping["down"], mapping["flat"], mapping["up"]]
    label_names = ["down", "flat", "up"]

    train_y_enc = encode_labels_for_preview(train_y, default_future_direction_8_encoding()).astype(int)
    holdout_y_enc = encode_labels_for_preview(holdout_y, default_future_direction_8_encoding()).astype(int)

    audit_train = audit_feature_values(train_x)
    audit_holdout = audit_feature_values(holdout_x)

    train_x_s, san_train = sanitize_features_for_model(train_x)
    holdout_x_s, san_holdout = sanitize_features_for_model(holdout_x)

    model_family_requested, model_family_used, model = _make_model(model_family, random_state, warnings)
    model.fit(train_x_s, train_y_enc)

    holdout_pred = model.predict(holdout_x_s)
    holdout_proba = model.predict_proba(holdout_x_s) if hasattr(model, "predict_proba") else None

    holdout_metrics = compute_classification_metrics(
        y_true=holdout_y_enc,
        y_pred=holdout_pred,
        labels=labels,
        label_names=label_names,
    )

    holdout_frame = dataset.holdout_frame
    holdout_pred_df = _build_prediction_frame(
        holdout_frame,
        summary.label_col,
        holdout_y_enc,
        holdout_pred,
        inv_mapping,
        holdout_proba,
    )

    model_filename = "model.joblib"
    model_path = run_dir / model_filename
    try:
        import joblib

        joblib.dump(model, model_path)
    except Exception:
        model_filename = "model.pkl"
        model_path = run_dir / model_filename
        with model_path.open("wb") as f:
            pickle.dump(model, f)
        warnings.append("joblib unavailable; wrote pickle model artifact instead.")

    _write_json(run_dir / "run_manifest.json", {
        "run_name": run_name,
        "phase": "phase35",
        "scope": "external_holdout_classification_validation",
        "training_executed": True,
        "holdout_evaluation_executed": True,
        "qlib_workflow_executed": False,
        "trading_backtest_profit_outputs": False,
    })
    _write_json(run_dir / "training_config.json", {
        "train_path": str(Path(train_path).expanduser().resolve()),
        "holdout_path": str(Path(holdout_path).expanduser().resolve()),
        "model_family": model_family_requested,
        "random_state": random_state,
    })
    _write_json(run_dir / "external_holdout_dataset_summary.json", summary.to_dict())
    _write_json(run_dir / "feature_columns.json", {"feature_columns": dataset.feature_columns})
    _write_json(run_dir / "label_encoding.json", {"mapping": mapping, "label_col": summary.label_col})
    _write_json(run_dir / "label_distribution_train.json", summary.label_distribution_train)
    _write_json(run_dir / "label_distribution_holdout.json", summary.label_distribution_holdout)
    _write_json(run_dir / "metrics_holdout.json", holdout_metrics)
    pd.DataFrame(holdout_metrics["confusion_matrix"]["rows"]).to_csv(run_dir / "confusion_matrix_holdout.csv", index=False)
    holdout_pred_df.to_csv(run_dir / "predictions_holdout.csv", index=False)
    _write_json(run_dir / "feature_value_audit_train.json", audit_train.to_dict())
    _write_json(run_dir / "feature_value_audit_holdout.json", audit_holdout.to_dict())
    _write_json(run_dir / "numeric_sanitization_train.json", san_train.to_dict())
    _write_json(run_dir / "numeric_sanitization_holdout.json", san_holdout.to_dict())
    _write_json(run_dir / "model_metadata.json", {
        "model_family_requested": model_family_requested,
        "model_family_used": model_family_used,
        "feature_count": len(dataset.feature_columns),
        "target_label": summary.label_col,
        "train_rows": summary.train_rows,
        "holdout_rows": summary.holdout_rows,
        "training_executed": True,
        "holdout_evaluation_executed": True,
    })

    artifact_files = sorted(p.name for p in run_dir.glob("*") if p.is_file())

    append_run_registry_record(
        registry_path="tmp/cajas/run_registry/runs.jsonl",
        record=RunRegistryRecord(
            run_id=build_run_id(run_name=run_name, run_type="external_holdout_training"),
            run_name=run_name,
            run_type="external_holdout_training",
            phase="phase35",
            status="completed",
            output_dir=str(run_dir),
            artifact_files=artifact_files,
            created_by="codex",
            training_executed=True,
            model_artifact_created=True,
            notes=["External holdout classification validation run."],
        ),
    )

    return ExternalHoldoutTrainingReport(
        run_name=run_name,
        model_family_requested=model_family_requested,
        model_family_used=model_family_used,
        target_label=summary.label_col,
        feature_count=len(dataset.feature_columns),
        train_rows=summary.train_rows,
        holdout_rows=summary.holdout_rows,
        train_time_range=summary.train_time_range,
        holdout_time_range=summary.holdout_time_range,
        training_executed=True,
        holdout_evaluation_executed=True,
        model_artifact_created=True,
        prediction_artifacts_created=True,
        metrics_artifacts_created=True,
        output_dir=str(run_dir),
        artifact_files=artifact_files,
        holdout_metrics=holdout_metrics,
        label_distribution_train=summary.label_distribution_train,
        label_distribution_holdout=summary.label_distribution_holdout,
        warnings=warnings,
        blockers=blockers,
    )
