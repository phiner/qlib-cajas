"""Classification metrics helpers for model bridge artifacts."""

from __future__ import annotations

from collections import Counter

from sklearn.metrics import accuracy_score, f1_score


def compute_classification_metrics(*, y_true: list, y_pred: list) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "label_distribution_true": {str(k): int(v) for k, v in Counter(y_true).items()},
        "label_distribution_pred": {str(k): int(v) for k, v in Counter(y_pred).items()},
    }
