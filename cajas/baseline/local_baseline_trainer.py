"""Controlled local baseline classification training for market-recognition research."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import pickle
from typing import Any

import pandas as pd
import yaml

from cajas.baseline.classification_metrics import compute_classification_metrics
from cajas.baseline.label_encoding import default_future_direction_8_encoding, encode_labels_for_preview
from cajas.config.experiment_config import build_workflow_config, load_experiment_config
from cajas.datasets.prepared_dataset import PreparedDataset
from cajas.handlers.prepared_csv_handler import PreparedCsvHandler
from cajas.registry.run_registry import (
    RunRegistryRecord,
    append_run_registry_record,
    build_run_id,
)


@dataclass(frozen=True)
class LocalBaselineTrainingConfig:
    config_path: str
    output_dir: str
    run_name: str
    model_family: str
    input_override: str | None = None
    random_state: int = 42

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LocalBaselineTrainingReport:
    config_name: str
    run_name: str
    model_family_requested: str
    model_family_used: str
    target_label: str
    feature_count: int
    train_rows: int
    valid_rows: int
    test_rows: int
    training_executed: bool
    model_artifact_created: bool
    prediction_artifacts_created: bool
    metrics_artifacts_created: bool
    output_dir: str
    artifact_files: list[str]
    metrics: dict
    label_distribution: dict
    warnings: list[str]
    blockers: list[str]
    qlib_workflow_executed: bool
    trading_backtest_profit_outputs: bool
    run_registry_path: str

    def to_dict(self) -> dict:
        return asdict(self)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _encode_labels(series: pd.Series, label_col: str) -> pd.Series:
    plan = default_future_direction_8_encoding(label_col=label_col)
    return encode_labels_for_preview(series, plan).astype(int)


def _load_local_training_policy(config_path: str) -> dict[str, Any]:
    root = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(root, dict):
        raise ValueError("config root must be a mapping")
    policy = root.get("local_baseline_training")
    if policy is None:
        return {}
    if not isinstance(policy, dict):
        raise ValueError("local_baseline_training must be a mapping")
    return policy


def _make_model(model_family: str, random_state: int, warnings: list[str]):
    requested = model_family.strip() or "LightGBM"
    lowered = requested.lower()

    if lowered == "lightgbm":
        try:
            from lightgbm import LGBMClassifier

            model = LGBMClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=-1,
                random_state=random_state,
                n_jobs=-1,
            )
            return requested, "LightGBM", model
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"LightGBM unavailable or failed to initialize: {exc}")

    if lowered in {"randomforest", "random_forest", "sklearn_random_forest"}:
        from sklearn.ensemble import RandomForestClassifier

        model = RandomForestClassifier(
            n_estimators=300,
            random_state=random_state,
            n_jobs=-1,
            min_samples_leaf=2,
        )
        return requested, "RandomForest", model

    if lowered in {"histgradientboosting", "hist_gradient_boosting"}:
        from sklearn.ensemble import HistGradientBoostingClassifier

        model = HistGradientBoostingClassifier(
            random_state=random_state,
            max_depth=8,
            learning_rate=0.08,
        )
        return requested, "HistGradientBoosting", model

    from sklearn.ensemble import RandomForestClassifier

    warnings.append(f"Unsupported model family '{requested}', falling back to RandomForest.")
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    return requested, "RandomForest", model


def _build_prediction_frame(
    *,
    segment_df: pd.DataFrame,
    label_col: str,
    y_true_encoded: pd.Series,
    y_pred_encoded,
    inv_mapping: dict[int, str],
    proba,
) -> pd.DataFrame:
    cols: list[str] = []
    for key in ("datetime", "symbol", "timeframe"):
        if key in segment_df.columns:
            cols.append(key)

    out = segment_df[cols].copy() if cols else pd.DataFrame(index=segment_df.index)
    out["label"] = segment_df[label_col].astype(str).values
    out["encoded_label"] = y_true_encoded.astype(int).values
    pred_encoded_series = pd.Series(y_pred_encoded, index=segment_df.index).astype(int)
    out["predicted_encoded_label"] = pred_encoded_series.values
    out["predicted_label"] = pred_encoded_series.map(inv_mapping).fillna("unknown").values

    if proba is not None:
        for class_idx, class_name in inv_mapping.items():
            if class_idx < proba.shape[1]:
                out[f"proba_{class_name}"] = proba[:, class_idx]

    return out


def train_local_baseline(
    *,
    config_path: str,
    output_dir: str | Path,
    run_name: str,
    input_override: str | None = None,
    model_family: str = "LightGBM",
    random_state: int = 42,
) -> LocalBaselineTrainingReport:
    warnings: list[str] = []
    blockers: list[str] = []

    cfg = load_experiment_config(config_path)
    policy = _load_local_training_policy(config_path)
    wf_cfg = build_workflow_config(cfg, csv_path_override=input_override)
    if not wf_cfg.label_col:
        raise ValueError("label_col is required for local baseline training")
    if policy and not bool(policy.get("enabled", False)):
        raise ValueError("local_baseline_training.enabled must be true for this run")

    out_base = Path(output_dir).expanduser().resolve()
    run_dir = out_base / run_name
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    dataset = PreparedDataset(csv_path=wf_cfg.csv_path, label_col=wf_cfg.label_col, segments=wf_cfg.segments)
    handler = PreparedCsvHandler(csv_path=wf_cfg.csv_path, label_col=wf_cfg.label_col)

    train_x, train_y = dataset.prepare("train")
    valid_x, valid_y = dataset.prepare("valid")
    test_x, test_y = dataset.prepare("test")

    train_seg_df = handler.prepare_segment(*wf_cfg.segments["train"])
    valid_seg_df = handler.prepare_segment(*wf_cfg.segments["valid"])
    test_seg_df = handler.prepare_segment(*wf_cfg.segments["test"])

    train_y_enc = _encode_labels(train_y, wf_cfg.label_col)
    valid_y_enc = _encode_labels(valid_y, wf_cfg.label_col)
    test_y_enc = _encode_labels(test_y, wf_cfg.label_col)

    mapping = default_future_direction_8_encoding(label_col=wf_cfg.label_col).mapping
    inv_mapping = {value: key for key, value in mapping.items()}
    labels = [mapping["down"], mapping["flat"], mapping["up"]]
    label_names = ["down", "flat", "up"]

    model_family_requested, model_family_used, model = _make_model(model_family, random_state, warnings)

    model.fit(train_x, train_y_enc)

    valid_pred = model.predict(valid_x)
    test_pred = model.predict(test_x)

    valid_proba = model.predict_proba(valid_x) if hasattr(model, "predict_proba") else None
    test_proba = model.predict_proba(test_x) if hasattr(model, "predict_proba") else None

    valid_metrics = compute_classification_metrics(
        y_true=valid_y_enc,
        y_pred=valid_pred,
        labels=labels,
        label_names=label_names,
    )
    test_metrics = compute_classification_metrics(
        y_true=test_y_enc,
        y_pred=test_pred,
        labels=labels,
        label_names=label_names,
    )

    label_distribution = {
        "train": handler.label_distribution(train_seg_df),
        "valid": handler.label_distribution(valid_seg_df),
        "test": handler.label_distribution(test_seg_df),
    }

    valid_predictions = _build_prediction_frame(
        segment_df=valid_seg_df,
        label_col=wf_cfg.label_col,
        y_true_encoded=valid_y_enc,
        y_pred_encoded=valid_pred,
        inv_mapping=inv_mapping,
        proba=valid_proba,
    )
    test_predictions = _build_prediction_frame(
        segment_df=test_seg_df,
        label_col=wf_cfg.label_col,
        y_true_encoded=test_y_enc,
        y_pred_encoded=test_pred,
        inv_mapping=inv_mapping,
        proba=test_proba,
    )

    model_filename = "model.joblib"
    model_path = run_dir / model_filename
    try:
        import joblib

        joblib.dump(model, model_path)
    except Exception:  # noqa: BLE001
        model_filename = "model.pkl"
        model_path = run_dir / model_filename
        with model_path.open("wb") as handle:
            pickle.dump(model, handle)
        warnings.append("joblib unavailable; wrote pickle model artifact instead.")

    _write_json(
        run_dir / "run_manifest.json",
        {
            "run_name": run_name,
            "phase": "phase20",
            "scope": "market_recognition_classification_only",
            "training_executed": True,
            "qlib_workflow_executed": False,
            "trading_backtest_profit_outputs": False,
        },
    )
    _write_json(
        run_dir / "training_config.json",
        LocalBaselineTrainingConfig(
            config_path=config_path,
            output_dir=str(out_base),
            run_name=run_name,
            model_family=model_family_requested,
            input_override=input_override,
            random_state=random_state,
        ).to_dict(),
    )
    _write_json(run_dir / "feature_columns.json", {"feature_columns": dataset.feature_columns})
    _write_json(run_dir / "label_encoding.json", {"mapping": mapping, "label_col": wf_cfg.label_col})
    _write_json(run_dir / "label_distribution.json", label_distribution)
    _write_json(run_dir / "metrics_valid.json", valid_metrics)
    _write_json(run_dir / "metrics_test.json", test_metrics)

    pd.DataFrame(valid_metrics["confusion_matrix"]["rows"]).to_csv(
        run_dir / "confusion_matrix_valid.csv", index=False
    )
    pd.DataFrame(test_metrics["confusion_matrix"]["rows"]).to_csv(
        run_dir / "confusion_matrix_test.csv", index=False
    )
    valid_predictions.to_csv(run_dir / "predictions_valid.csv", index=False)
    test_predictions.to_csv(run_dir / "predictions_test.csv", index=False)

    _write_json(
        run_dir / "model_metadata.json",
        {
            "model_family_requested": model_family_requested,
            "model_family_used": model_family_used,
            "random_state": random_state,
            "feature_count": len(dataset.feature_columns),
            "train_rows": int(len(train_x)),
            "valid_rows": int(len(valid_x)),
            "test_rows": int(len(test_x)),
            "target_label": wf_cfg.label_col,
            "training_executed": True,
            "notes": [
                "Local baseline classification model for market-recognition research.",
                "No trading/backtest/profit analysis outputs are produced.",
            ],
        },
    )

    artifact_files = sorted(path.name for path in run_dir.glob("*") if path.is_file())

    registry_path = str(
        policy.get("output", {}).get("registry_path", "tmp/cajas/run_registry/runs.jsonl")
        if isinstance(policy.get("output", {}), dict)
        else "tmp/cajas/run_registry/runs.jsonl"
    )
    append_run_registry_record(
        registry_path=registry_path,
        record=RunRegistryRecord(
            run_id=build_run_id(run_name=run_name, run_type="local_baseline_training"),
            run_name=run_name,
            run_type="local_baseline_training",
            phase="phase20",
            status="completed",
            output_dir=str(run_dir),
            artifact_files=artifact_files,
            created_by="codex",
            training_executed=True,
            model_artifact_created=True,
            notes=[
                "Classification-only baseline run.",
                "No trading/backtest/profit analysis executed.",
            ],
        ),
    )

    return LocalBaselineTrainingReport(
        config_name=cfg.name,
        run_name=run_name,
        model_family_requested=model_family_requested,
        model_family_used=model_family_used,
        target_label=wf_cfg.label_col,
        feature_count=len(dataset.feature_columns),
        train_rows=int(len(train_x)),
        valid_rows=int(len(valid_x)),
        test_rows=int(len(test_x)),
        training_executed=True,
        model_artifact_created=True,
        prediction_artifacts_created=True,
        metrics_artifacts_created=True,
        output_dir=str(run_dir),
        artifact_files=artifact_files,
        metrics={"valid": valid_metrics, "test": test_metrics},
        label_distribution=label_distribution,
        warnings=warnings,
        blockers=blockers,
        qlib_workflow_executed=False,
        trading_backtest_profit_outputs=False,
        run_registry_path=str(Path(registry_path).expanduser().resolve()),
    )
