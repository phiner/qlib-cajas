"""Flat-class diagnosis helpers for classification prediction artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class FlatClassDiagnosisReport:
    run_dir: str
    split: str
    flat_support: int
    flat_predictions: int
    total_rows: int
    flat_support_ratio: float
    flat_prediction_ratio: float
    warnings: list[str]
    recommendations: list[str]
    trading_conclusions_present: bool

    def to_dict(self) -> dict:
        return asdict(self)


def diagnose_flat_class(
    *,
    prediction_csv: str | Path,
    split: str,
    flat_label: str = "flat",
) -> FlatClassDiagnosisReport:
    path = Path(prediction_csv).expanduser().resolve()
    df = pd.read_csv(path)
    if "label" not in df.columns or "predicted_label" not in df.columns:
        raise ValueError("prediction csv must include 'label' and 'predicted_label' columns")

    total_rows = int(len(df))
    flat_support = int((df["label"].astype(str) == flat_label).sum())
    flat_predictions = int((df["predicted_label"].astype(str) == flat_label).sum())
    support_ratio = (flat_support / total_rows) if total_rows else 0.0
    prediction_ratio = (flat_predictions / total_rows) if total_rows else 0.0

    warnings: list[str] = []
    if support_ratio < 0.01:
        warnings.append("flat support ratio is below 1%; class is highly imbalanced")
    if flat_predictions == 0:
        warnings.append("model predicted zero flat rows")
    if flat_support > 0 and flat_predictions == 0:
        warnings.append("flat recall is effectively zero in this artifact")

    recommendations = [
        "consider threshold-based flat label definition",
        "compare binary up/down label against three-class label",
        "compare horizon-specific label distributions (4/8/16)",
        "collect more flat-like examples before rebalancing",
        "inspect feature separability for flat class",
    ]

    return FlatClassDiagnosisReport(
        run_dir=str(path.parent),
        split=split,
        flat_support=flat_support,
        flat_predictions=flat_predictions,
        total_rows=total_rows,
        flat_support_ratio=support_ratio,
        flat_prediction_ratio=prediction_ratio,
        warnings=warnings,
        recommendations=recommendations,
        trading_conclusions_present=False,
    )
