"""Generate threshold-based future direction labels for multiple horizons."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ThresholdLabelSpec:
    horizon: int
    threshold: float
    label_col: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ThresholdLabelGenerationReport:
    input_path: str
    output_path: str | None
    specs: list[dict]
    row_count: int
    label_distributions: dict[str, dict[str, int]]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _fmt_threshold(threshold: float) -> str:
    s = f"{threshold:.5f}".rstrip("0").rstrip(".")
    if "." not in s:
        s = s + ".0"
    return s.replace("-", "m").replace(".", "_")


def build_threshold_label_col(horizon: int, threshold: float) -> str:
    return f"future_direction_{horizon}_thr_{_fmt_threshold(threshold)}"


def generate_threshold_labels(
    *,
    input_path: str | Path,
    horizons: list[int],
    thresholds: list[float],
    output_path: str | Path | None = None,
    close_col: str = "close",
) -> ThresholdLabelGenerationReport:
    src = Path(input_path).expanduser().resolve()
    df = pd.read_csv(src)
    if close_col not in df.columns:
        raise ValueError(f"missing close column: {close_col}")
    close = pd.to_numeric(df[close_col], errors="coerce")
    out = df.copy()
    specs: list[ThresholdLabelSpec] = []
    distributions: dict[str, dict[str, int]] = {}
    warnings: list[str] = []

    for horizon in horizons:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        fut = close.shift(-horizon)
        fut_ret = (fut / close) - 1.0
        for threshold in thresholds:
            if threshold < 0:
                raise ValueError("threshold must be non-negative")
            label_col = build_threshold_label_col(horizon, threshold)
            labels = pd.Series("flat", index=out.index, dtype="string")
            labels[fut_ret > threshold] = "up"
            labels[fut_ret < -threshold] = "down"
            labels[fut_ret.isna()] = pd.NA
            out[label_col] = labels
            counts = labels.dropna().value_counts().to_dict()
            distributions[label_col] = {str(k): int(v) for k, v in counts.items()}
            specs.append(ThresholdLabelSpec(horizon=horizon, threshold=threshold, label_col=label_col))
            flat_ratio = distributions[label_col].get("flat", 0) / max(sum(distributions[label_col].values()), 1)
            if flat_ratio < 0.005:
                warnings.append(f"{label_col} flat ratio below 0.5%")

    out_path = None
    if output_path is not None:
        out_path = str(Path(output_path).expanduser().resolve())
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(out_path, index=False)

    return ThresholdLabelGenerationReport(
        input_path=str(src),
        output_path=out_path,
        specs=[s.to_dict() for s in specs],
        row_count=int(len(out)),
        label_distributions=distributions,
        warnings=warnings,
    )
