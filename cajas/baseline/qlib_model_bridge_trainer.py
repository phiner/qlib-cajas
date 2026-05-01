"""CPU-only baseline trainer for qlib model experiment bridge."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from cajas.reports.qlib_model_metrics import compute_classification_metrics


def _split_by_ratio(df: pd.DataFrame, split_ratios: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    n = len(df)
    if n < 3:
        raise ValueError("at least 3 rows are required for train/valid/test split")
    train_n = int(n * float(split_ratios.get("train", 0.7)))
    valid_n = int(n * float(split_ratios.get("valid", 0.15)))
    test_n = n - train_n - valid_n

    if train_n <= 0:
        train_n = 1
    if valid_n <= 0:
        valid_n = 1
    if test_n <= 0:
        test_n = 1

    total = train_n + valid_n + test_n
    if total > n:
        overflow = total - n
        reduce_train = min(overflow, max(train_n - 1, 0))
        train_n -= reduce_train
        overflow -= reduce_train
        if overflow > 0:
            reduce_valid = min(overflow, max(valid_n - 1, 0))
            valid_n -= reduce_valid
            overflow -= reduce_valid
        if overflow > 0:
            test_n -= overflow

    train_end = train_n
    valid_end = train_end + valid_n
    train = df.iloc[:train_end]
    valid = df.iloc[train_end:valid_end]
    test = df.iloc[valid_end:]
    return train, valid, test


def train_qlib_model_bridge_baseline(*, contract: dict, out_dir: str | Path, seed: int = 42, max_rows: int = 5000) -> dict:
    if contract.get("readiness_status") == "blocked":
        raise ValueError("training contract is blocked")

    hp = Path(contract["handler_input_path"]).expanduser().resolve()
    df = pd.read_csv(hp)
    if max_rows > 0 and len(df) > max_rows:
        df = df.iloc[:max_rows].copy()

    dt_col = contract["datetime_col"]
    if dt_col in df.columns:
        df = df.sort_values(dt_col, kind="stable")

    label_col = contract["label_col"]
    feature_cols = [c for c in contract["feature_columns"] if c in df.columns]
    if not feature_cols:
        raise ValueError("no feature columns available for training")

    train_df, valid_df, test_df = _split_by_ratio(df, contract.get("split_ratios", {}))
    if len(train_df) == 0 or len(valid_df) == 0 or len(test_df) == 0:
        raise ValueError("insufficient rows for train/valid/test split")

    x_train = train_df[feature_cols]
    y_train = train_df[label_col]
    x_valid = valid_df[feature_cols]
    y_valid = valid_df[label_col]
    x_test = test_df[feature_cols]
    y_test = test_df[label_col]

    model = RandomForestClassifier(n_estimators=64, random_state=seed, n_jobs=1)
    model.fit(x_train, y_train)

    pred_valid = model.predict(x_valid)
    pred_test = model.predict(x_test)

    metrics_valid = compute_classification_metrics(y_true=list(y_valid), y_pred=list(pred_valid))
    metrics_test = compute_classification_metrics(y_true=list(y_test), y_pred=list(pred_test))

    pred_frame = pd.DataFrame(
        {
            "split": ["valid"] * len(valid_df) + ["test"] * len(test_df),
            "y_true": list(y_valid) + list(y_test),
            "y_pred": list(pred_valid) + list(pred_test),
        }
    )

    out = Path(out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    pred_path = out / "predictions.csv"
    pred_frame.to_csv(pred_path, index=False)

    return {
        "metrics_valid": metrics_valid,
        "metrics_test": metrics_test,
        "split_summary": {"train": int(len(train_df)), "valid": int(len(valid_df)), "test": int(len(test_df))},
        "feature_columns": feature_cols,
        "label_col": label_col,
        "predictions_path": str(pred_path),
        "model_family": "RandomForestClassifier",
        "seed": seed,
    }
