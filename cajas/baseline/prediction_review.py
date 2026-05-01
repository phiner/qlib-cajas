"""Prediction review reports for local baseline classification outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class PredictionReviewReport:
    split: str
    total_rows: int
    correct_rows: int
    error_rows: int
    accuracy: float
    low_confidence_count: int
    high_confidence_error_count: int
    per_class_errors: dict[str, int]
    output_files: dict[str, str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def build_prediction_review(
    *,
    prediction_csv: str | Path,
    output_dir: str | Path,
    split: str,
    low_confidence_threshold: float = 0.45,
    high_confidence_error_threshold: float = 0.70,
) -> PredictionReviewReport:
    src = Path(prediction_csv).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(f"Prediction CSV not found: {src}")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src)
    for col in ("label", "predicted_label"):
        if col not in df.columns:
            raise ValueError(f"Prediction CSV missing required column: {col}")

    df = df.copy()
    df["label"] = df["label"].astype(str)
    df["predicted_label"] = df["predicted_label"].astype(str)
    df["is_correct"] = df["label"] == df["predicted_label"]

    total_rows = int(len(df))
    correct_rows = int(df["is_correct"].sum())
    error_rows = int(total_rows - correct_rows)
    accuracy = float(correct_rows / total_rows) if total_rows > 0 else 0.0

    proba_cols = [c for c in df.columns if c.startswith("proba_")]
    warnings: list[str] = []

    if proba_cols:
        df["max_confidence"] = df[proba_cols].max(axis=1)
        low_conf = df[df["max_confidence"] <= float(low_confidence_threshold)].copy()
        high_conf_err = df[(~df["is_correct"]) & (df["max_confidence"] >= float(high_confidence_error_threshold))].copy()
    else:
        warnings.append("Probability columns are missing; confidence-based outputs are empty.")
        low_conf = df.iloc[0:0].copy()
        high_conf_err = df.iloc[0:0].copy()

    error_df = df[~df["is_correct"]].copy()
    per_class = error_df.groupby("label").size().sort_index().to_dict()
    per_class_errors = {str(k): int(v) for k, v in per_class.items()}

    summary_rows = [{"label": label, "error_count": count} for label, count in per_class_errors.items()]
    summary_df = pd.DataFrame(summary_rows, columns=["label", "error_count"])

    low_path = out_dir / f"{split}_low_confidence_samples.csv"
    high_path = out_dir / f"{split}_high_confidence_errors.csv"
    summary_path = out_dir / f"{split}_error_summary_by_class.csv"
    report_path = out_dir / f"{split}_prediction_review_report.json"

    low_conf.to_csv(low_path, index=False)
    high_conf_err.to_csv(high_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    report = PredictionReviewReport(
        split=split,
        total_rows=total_rows,
        correct_rows=correct_rows,
        error_rows=error_rows,
        accuracy=accuracy,
        low_confidence_count=int(len(low_conf)),
        high_confidence_error_count=int(len(high_conf_err)),
        per_class_errors=per_class_errors,
        output_files={
            "low_confidence_samples_csv": str(low_path),
            "high_confidence_errors_csv": str(high_path),
            "error_summary_by_class_csv": str(summary_path),
            "prediction_review_report_json": str(report_path),
        },
        warnings=warnings,
    )

    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
