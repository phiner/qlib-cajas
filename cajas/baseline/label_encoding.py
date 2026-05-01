"""Label encoding preview helpers for future multiclass baseline training."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class LabelEncodingPlan:
    label_col: str
    mapping: dict[str, int]
    unknown_label_policy: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LabelEncodingPreview:
    label_col: str
    mapping: dict[str, int]
    encoded_count: int
    class_counts: dict[str, int]
    encoded_class_counts: dict[int, int]
    unknown_labels: list[str]
    missing_count: int
    issues: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


def default_future_direction_8_encoding(
    label_col: str = "future_direction_8",
) -> LabelEncodingPlan:
    return LabelEncodingPlan(
        label_col=label_col,
        mapping={"down": 0, "flat": 1, "up": 2},
        unknown_label_policy="error",
    )


def preview_label_encoding(labels: Iterable, plan: LabelEncodingPlan) -> LabelEncodingPreview:
    series = pd.Series(labels, copy=True)
    missing_mask = series.isna()
    missing_count = int(missing_mask.sum())

    non_missing = series[~missing_mask].astype(str)
    class_counts_series = non_missing.value_counts().sort_index()
    class_counts = {str(k): int(v) for k, v in class_counts_series.items()}

    known = set(plan.mapping)
    unknown_labels = sorted({label for label in class_counts if label not in known})

    issues: list[dict] = []
    if missing_count > 0:
        issues.append(
            {
                "severity": "error",
                "code": "missing_labels",
                "message": f"Missing labels found: {missing_count}",
                "count": missing_count,
            }
        )
    if unknown_labels:
        issues.append(
            {
                "severity": "error",
                "code": "unknown_labels",
                "message": "Unknown labels found.",
                "labels": unknown_labels,
            }
        )

    encoded_class_counts: dict[int, int] = {}
    encoded_count = 0
    if not issues:
        encoded = encode_labels_for_preview(series, plan)
        encoded_non_missing = encoded[~encoded.isna()].astype(int)
        encoded_counts_series = encoded_non_missing.value_counts().sort_index()
        encoded_class_counts = {int(k): int(v) for k, v in encoded_counts_series.items()}
        encoded_count = int(encoded_non_missing.shape[0])

    return LabelEncodingPreview(
        label_col=plan.label_col,
        mapping=dict(plan.mapping),
        encoded_count=encoded_count,
        class_counts=class_counts,
        encoded_class_counts=encoded_class_counts,
        unknown_labels=unknown_labels,
        missing_count=missing_count,
        issues=issues,
    )


def encode_labels_for_preview(labels: Iterable, plan: LabelEncodingPlan) -> pd.Series:
    series = pd.Series(labels, copy=True)
    encoded = pd.Series(index=series.index, dtype="Int64")

    missing_mask = series.isna()
    non_missing = series[~missing_mask].astype(str)

    unknown_mask = ~non_missing.isin(plan.mapping.keys())
    if bool(unknown_mask.any()):
        unknown_values = sorted(non_missing[unknown_mask].unique().tolist())
        raise ValueError(
            "Unknown labels found for encoding: " + ", ".join(str(v) for v in unknown_values)
        )
    if int(missing_mask.sum()) > 0:
        raise ValueError(f"Missing labels found for encoding: {int(missing_mask.sum())}")

    encoded.loc[~missing_mask] = non_missing.map(plan.mapping).astype("Int64")
    return encoded
