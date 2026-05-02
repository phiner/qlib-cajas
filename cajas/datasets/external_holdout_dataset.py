"""External holdout dataset adapter: train period and holdout period are separated."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype

from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision


@dataclass(frozen=True)
class ExternalHoldoutDatasetSummary:
    train_path: str
    holdout_path: str
    label_col: str
    feature_count: int
    train_rows: int
    holdout_rows: int
    train_time_range: dict
    holdout_time_range: dict
    leakage_columns_in_features: list[str]
    label_distribution_train: dict
    label_distribution_holdout: dict

    def to_dict(self) -> dict:
        return asdict(self)


class ExternalHoldoutDataset:
    def __init__(
        self,
        *,
        train_path: str | Path,
        holdout_path: str | Path,
        label_col: str = "future_direction_8",
        leakage_columns: tuple[str, ...] = ("future_close_8", "future_return_8"),
        row_limit: int | None = None,
        allow_large_data: bool = False,
    ) -> None:
        self._train_path = Path(train_path).expanduser().resolve()
        self._holdout_path = Path(holdout_path).expanduser().resolve()
        self._label_col = label_col
        self._leakage = tuple(leakage_columns)
        self._row_limit = row_limit
        self._allow_large_data = allow_large_data

        self._train_df = self._load(self._train_path)
        self._holdout_df = self._load(self._holdout_path)
        self._feature_columns = self._resolve_feature_columns()
        self._assert_no_overlap()

    def _load(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(f"Prepared dataset not found: {path}")
        
        # Policy guard for large data reads
        policy = CsvLoadingPolicy(row_limit=self._row_limit, allow_large_data=self._allow_large_data)
        decision = evaluate_loading_decision(path, policy)
        
        if not decision["can_full_read"] and self._row_limit is None:
            raise ValueError(f"CSV requires row_limit or allow_large_data: {decision['warnings']}")
        
        read_kwargs = {}
        if self._row_limit is not None:
            read_kwargs["nrows"] = self._row_limit
        
        df = pd.read_csv(path, **read_kwargs)
        if self._label_col not in df.columns:
            raise ValueError(f"Label column not found: {self._label_col}")
        if "datetime" not in df.columns:
            raise ValueError("datetime column is required")
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
        if int(df["datetime"].isna().sum()) > 0:
            raise ValueError(f"Invalid datetime values in {path}")
        return df.sort_values("datetime").reset_index(drop=True)

    def _resolve_feature_columns(self) -> list[str]:
        excluded = {"datetime", "symbol", "timeframe", self._label_col, *self._leakage}
        cols = [
            c
            for c in self._train_df.columns
            if c in self._holdout_df.columns and c not in excluded and is_numeric_dtype(self._train_df[c])
        ]
        if not cols:
            raise ValueError("No numeric feature columns available for external holdout dataset")
        return sorted(cols)

    def _assert_no_overlap(self) -> None:
        train_times = set(self._train_df["datetime"])
        holdout_times = set(self._holdout_df["datetime"])
        overlap = train_times.intersection(holdout_times)
        if overlap:
            raise ValueError(f"Train and holdout datetime overlap detected: {len(overlap)} rows")

    @property
    def feature_columns(self) -> list[str]:
        return list(self._feature_columns)

    def prepare_train(self):
        return self._train_df[self.feature_columns].copy(), self._train_df[self._label_col].copy()

    def prepare_holdout(self):
        return self._holdout_df[self.feature_columns].copy(), self._holdout_df[self._label_col].copy()

    def summary(self) -> ExternalHoldoutDatasetSummary:
        leakage_in_feat = sorted(set(self.feature_columns).intersection(self._leakage))
        return ExternalHoldoutDatasetSummary(
            train_path=str(self._train_path),
            holdout_path=str(self._holdout_path),
            label_col=self._label_col,
            feature_count=len(self.feature_columns),
            train_rows=int(len(self._train_df)),
            holdout_rows=int(len(self._holdout_df)),
            train_time_range={
                "start": self._train_df["datetime"].min().isoformat(),
                "end": self._train_df["datetime"].max().isoformat(),
            },
            holdout_time_range={
                "start": self._holdout_df["datetime"].min().isoformat(),
                "end": self._holdout_df["datetime"].max().isoformat(),
            },
            leakage_columns_in_features=leakage_in_feat,
            label_distribution_train={str(k): int(v) for k, v in self._train_df[self._label_col].value_counts().sort_index().items()},
            label_distribution_holdout={str(k): int(v) for k, v in self._holdout_df[self._label_col].value_counts().sort_index().items()},
        )

    @property
    def train_frame(self) -> pd.DataFrame:
        return self._train_df.copy()

    @property
    def holdout_frame(self) -> pd.DataFrame:
        return self._holdout_df.copy()
