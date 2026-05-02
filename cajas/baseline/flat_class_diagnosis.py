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
    chunk_size: int = 50000,
) -> FlatClassDiagnosisReport:
    path = Path(prediction_csv).expanduser().resolve()
    
    # Chunked counting to avoid full read of large prediction artifacts
    total_rows = 0
    flat_support = 0
    flat_predictions = 0
    
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        if "label" not in chunk.columns or "predicted_label" not in chunk.columns:
            raise ValueError("prediction csv must include 'label' and 'predicted_label' columns")
        
        total_rows += len(chunk)
        flat_support += int((chunk["label"].astype(str) == flat_label).sum())
        flat_predictions += int((chunk["predicted_label"].astype(str) == flat_label).sum())
    
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
