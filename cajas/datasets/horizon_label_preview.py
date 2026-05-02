"""Preview alternative future_direction horizons from prepared datasets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class HorizonLabelDistribution:
    horizon: int
    label_col: str
    row_count: int
    distribution: dict[str, int]
    flat_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class HorizonLabelPreviewReport:
    input_path: str
    horizons: list[HorizonLabelDistribution]
    warnings: list[str]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["horizons"] = [h.to_dict() for h in self.horizons]
        return payload


def preview_horizon_labels(
    *,
    input_path: str | Path,
    horizons: list[int],
    close_col: str = "close",
    row_limit: int | None = None,
) -> HorizonLabelPreviewReport:
    path = Path(input_path).expanduser().resolve()
    read_kwargs = {}
    if row_limit is not None:
        read_kwargs["nrows"] = row_limit
    df = pd.read_csv(path, **read_kwargs)
    if close_col not in df.columns:
        raise ValueError(f"missing required close column: {close_col}")
    close = pd.to_numeric(df[close_col], errors="coerce")
    warnings: list[str] = []
    out: list[HorizonLabelDistribution] = []

    for horizon in horizons:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        fut = close.shift(-horizon)
        valid = close.notna() & fut.notna()
        future_ret = (fut[valid] / close[valid]) - 1.0
        labels = pd.Series("flat", index=future_ret.index, dtype="string")
        labels[future_ret > 0] = "up"
        labels[future_ret < 0] = "down"
        dist = labels.value_counts(dropna=False).to_dict()
        row_count = int(labels.shape[0])
        flat_count = int(dist.get("flat", 0))
        flat_ratio = (flat_count / row_count) if row_count else 0.0
        if flat_ratio < 0.0001:
            warnings.append(f"flat ratio is near zero for horizon {horizon}")
        out.append(
            HorizonLabelDistribution(
                horizon=horizon,
                label_col=f"future_direction_{horizon}",
                row_count=row_count,
                distribution={str(k): int(v) for k, v in dist.items()},
                flat_ratio=flat_ratio,
            )
        )

    return HorizonLabelPreviewReport(input_path=str(path), horizons=out, warnings=warnings)
