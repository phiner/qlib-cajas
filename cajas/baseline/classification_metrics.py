"""Classification-only metrics helpers for local baseline research training."""

from __future__ import annotations

from typing import Any

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def compute_classification_metrics(
    *,
    y_true,
    y_pred,
    labels: list[int],
    label_names: list[str],
) -> dict:
    if len(labels) != len(label_names):
        raise ValueError("labels and label_names must have the same length")

    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
    weighted_f1 = float(
        f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
    )

    precision, recall, f1_values, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    per_class: dict[str, dict[str, Any]] = {}
    for idx, name in enumerate(label_names):
        per_class[name] = {
            "precision": float(precision[idx]),
            "recall": float(recall[idx]),
            "f1": float(f1_values[idx]),
            "support": int(support[idx]),
        }

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    matrix_rows = confusion_matrix_to_rows(matrix=matrix, label_names=label_names)

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "labels": list(label_names),
        "confusion_matrix": {
            "labels": list(label_names),
            "matrix": [[int(v) for v in row] for row in matrix.tolist()],
            "rows": matrix_rows,
        },
    }


def confusion_matrix_to_rows(*, matrix, label_names: list[str]) -> list[dict]:
    rows: list[dict] = []
    for row_idx, true_label in enumerate(label_names):
        row_payload = {"true_label": true_label}
        for col_idx, pred_label in enumerate(label_names):
            row_payload[f"pred_{pred_label}"] = int(matrix[row_idx][col_idx])
        rows.append(row_payload)
    return rows
