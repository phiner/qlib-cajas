"""Minimal prepared CSV handler for cajas research workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from pandas.api.types import is_numeric_dtype


REQUIRED_COLUMNS = [
    "datetime",
    "symbol",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "future_direction_8",
]

LEAKAGE_COLUMNS = {"future_close_8", "future_return_8"}


class PreparedCsvHandler:
    """Load and validate a prepared CSV dataset for market-recognition research."""

    def __init__(self, csv_path: str, label_col: str = "future_direction_8") -> None:
        self._csv_path = Path(csv_path)
        self._label_col = label_col
        self._df = self._load_and_validate()
        self._feature_columns = self._resolve_feature_columns()

    @property
    def feature_columns(self) -> list[str]:
        return self._feature_columns

    @property
    def label_col(self) -> str:
        return self._label_col

    def summary(self) -> dict[str, Any]:
        return {
            "csv_path": str(self._csv_path),
            "row_count": int(len(self._df)),
            "time_start": self._df["datetime"].min().isoformat(),
            "time_end": self._df["datetime"].max().isoformat(),
            "duplicate_datetime_count": int(self._df["datetime"].duplicated().sum()),
            "sorted_by_datetime": bool(self._df["datetime"].is_monotonic_increasing),
            "required_columns": REQUIRED_COLUMNS,
            "feature_columns": self.feature_columns,
            "feature_count": len(self.feature_columns),
            "label_col": self.label_col,
            "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
        }

    def label_distribution(self, df: pd.DataFrame | None = None) -> dict[str, int]:
        data = self._df if df is None else df
        counts = data[self.label_col].value_counts(dropna=False).sort_index()
        return {str(k): int(v) for k, v in counts.items()}

    def prepare_segment(self, start: str, end: str) -> pd.DataFrame:
        start_dt = pd.to_datetime(start, utc=True)
        end_dt = pd.to_datetime(end, utc=True)
        segment = self._df[(self._df["datetime"] >= start_dt) & (self._df["datetime"] <= end_dt)]
        return segment.copy()

    def prepare_segments(self, segments: dict[str, tuple[str, str]]) -> dict[str, pd.DataFrame]:
        prepared: dict[str, pd.DataFrame] = {}
        for name, (start, end) in segments.items():
            prepared[name] = self.prepare_segment(start, end)
        return prepared

    def _load_and_validate(self) -> pd.DataFrame:
        if not self._csv_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {self._csv_path}")

        df = pd.read_csv(self._csv_path)
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        if self._label_col not in df.columns:
            raise ValueError(f"Label column not found: {self._label_col}")

        df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
        invalid_dt = int(df["datetime"].isna().sum())
        if invalid_dt > 0:
            raise ValueError(f"Invalid datetime rows found: {invalid_dt}")

        df = df.sort_values("datetime").reset_index(drop=True)
        dup_count = int(df["datetime"].duplicated().sum())
        if dup_count > 0:
            raise ValueError(f"Duplicate datetime rows found: {dup_count}")

        return df

    def _resolve_feature_columns(self) -> list[str]:
        excluded = {"datetime", "symbol", "timeframe", self.label_col} | LEAKAGE_COLUMNS
        features = [
            col
            for col in self._df.columns
            if col not in excluded and is_numeric_dtype(self._df[col])
        ]
        if not features:
            raise ValueError("No usable feature columns found after exclusions")
        return sorted(features)
