"""Confidence-bucket analysis for classification prediction artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ConfidenceBucketSummary:
    bucket: str
    row_count: int
    accuracy: float | None
    error_rate: float | None
    class_distribution: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ConfidenceAnalysisReport:
    split: str
    total_rows: int
    probability_columns: list[str]
    buckets: list[ConfidenceBucketSummary]
    warnings: list[str]
    trading_thresholds_created: bool

    def to_dict(self) -> dict:
        return {
            "split": self.split,
            "total_rows": self.total_rows,
            "probability_columns": self.probability_columns,
            "buckets": [b.to_dict() for b in self.buckets],
            "warnings": self.warnings,
            "trading_thresholds_created": self.trading_thresholds_created,
        }


def analyze_prediction_confidence(
    *,
    prediction_csv: str | Path,
    split: str,
    bucket_edges: list[float] | None = None,
) -> ConfidenceAnalysisReport:
    edges = bucket_edges or [0.0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    df = pd.read_csv(Path(prediction_csv).expanduser().resolve())
    warnings: list[str] = []

    total_rows = int(len(df))
    proba_cols = [c for c in df.columns if c.startswith("proba_")]
    if not proba_cols:
        warnings.append("Probability columns missing; confidence buckets unavailable.")
        return ConfidenceAnalysisReport(split, total_rows, [], [], warnings, False)

    work = df.copy()
    work["label"] = work["label"].astype(str)
    work["predicted_label"] = work["predicted_label"].astype(str)
    work["is_correct"] = work["label"] == work["predicted_label"]
    work["confidence"] = work[proba_cols].max(axis=1)

    bucket_col = pd.cut(
        work["confidence"],
        bins=edges,
        include_lowest=True,
        right=True,
        duplicates="drop",
    )

    summaries: list[ConfidenceBucketSummary] = []
    categories = bucket_col.cat.categories if hasattr(bucket_col, "cat") else []
    for interval in categories:
        sel = work[bucket_col == interval]
        row_count = int(len(sel))
        if row_count == 0:
            summaries.append(ConfidenceBucketSummary(str(interval), 0, None, None, {}))
            continue
        acc = float(sel["is_correct"].mean())
        err = float(1.0 - acc)
        dist = sel["label"].value_counts().sort_index().to_dict()
        summaries.append(
            ConfidenceBucketSummary(
                bucket=str(interval),
                row_count=row_count,
                accuracy=acc,
                error_rate=err,
                class_distribution={str(k): int(v) for k, v in dist.items()},
            )
        )

    return ConfidenceAnalysisReport(
        split=split,
        total_rows=total_rows,
        probability_columns=proba_cols,
        buckets=summaries,
        warnings=warnings,
        trading_thresholds_created=False,
    )
