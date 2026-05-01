"""Qlib-inspired prepared dataset adapter for research-only usage."""

from __future__ import annotations

from typing import Any

import pandas as pd

from cajas.handlers.prepared_csv_handler import LEAKAGE_COLUMNS, PreparedCsvHandler


DEFAULT_SEGMENTS = {
    "train": ("2025-01-01", "2025-08-31"),
    "valid": ("2025-09-01", "2025-10-31"),
    "test": ("2025-11-01", "2025-12-31"),
}


class PreparedDataset:
    """DatasetH-like adapter exposing segment-wise features/labels."""

    def __init__(
        self,
        csv_path: str,
        label_col: str = "future_direction_8",
        segments: dict[str, tuple[str, str]] | None = None,
    ) -> None:
        self._handler = PreparedCsvHandler(csv_path=csv_path, label_col=label_col)
        self._segments = segments or DEFAULT_SEGMENTS.copy()

    @property
    def feature_columns(self) -> list[str]:
        return self._handler.feature_columns

    @property
    def segments(self) -> dict[str, tuple[str, str]]:
        return dict(self._segments)

    def prepare(self, segment: str) -> tuple[pd.DataFrame, pd.Series]:
        if segment not in self._segments:
            raise ValueError(f"Unknown segment: {segment}")

        start, end = self._segments[segment]
        seg_df = self._handler.prepare_segment(start, end)
        if seg_df.empty:
            raise ValueError(f"Segment has zero rows: {segment}")

        features = seg_df[self.feature_columns].copy()
        labels = seg_df[self._handler.label_col].copy()

        if len(features) != len(labels):
            raise ValueError(f"Feature/label row mismatch in segment: {segment}")
        if not self.feature_columns:
            raise ValueError("No feature columns available")

        leakage_found = sorted(set(features.columns).intersection(LEAKAGE_COLUMNS))
        if leakage_found:
            raise ValueError(
                "Leakage columns found in features: " + ", ".join(leakage_found)
            )
        return features, labels

    def prepare_all(self) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
        return {name: self.prepare(name) for name in self._segments}

    def summary(self) -> dict[str, Any]:
        base = self._handler.summary()
        base["segments"] = self.segments
        return base
