"""Inspect model feature importance from baseline run artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class FeatureImportanceInspectionReport:
    run_dir: str
    available: bool
    feature_importance: list[dict]
    top_features: list[dict]
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def inspect_feature_importance(*, run_dir: str | Path, top_k: int = 30) -> FeatureImportanceInspectionReport:
    base = Path(run_dir).expanduser().resolve()
    model_path = base / "model.joblib"
    feature_path = base / "feature_columns.json"

    warnings: list[str] = []
    blockers: list[str] = []
    rows: list[dict] = []

    if not model_path.exists() or not feature_path.exists():
        return FeatureImportanceInspectionReport(
            run_dir=str(base),
            available=False,
            feature_importance=[],
            top_features=[],
            warnings=["Required model or feature columns artifact missing."],
            blockers=[],
        )

    try:
        import joblib

        model = joblib.load(model_path)
        feature_cols = json.loads(feature_path.read_text(encoding="utf-8")).get("feature_columns", [])
        importances = None
        if hasattr(model, "feature_importances_"):
            importances = list(model.feature_importances_)
        elif hasattr(model, "coef_"):
            coef = getattr(model, "coef_")
            import numpy as np

            importances = list(np.abs(coef).mean(axis=0)) if len(getattr(coef, "shape", [])) == 2 else list(np.abs(coef))

        if importances is None:
            warnings.append("Model does not expose feature importance.")
        else:
            for name, value in zip(feature_cols, importances):
                rows.append({"feature": str(name), "importance": float(value)})
            rows.sort(key=lambda x: x["importance"], reverse=True)
            total = sum(x["importance"] for x in rows) or 1.0
            for idx, row in enumerate(rows, start=1):
                row["rank"] = idx
                row["normalized_importance"] = float(row["importance"] / total)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"Failed to inspect feature importance: {exc}")

    return FeatureImportanceInspectionReport(
        run_dir=str(base),
        available=bool(rows),
        feature_importance=rows,
        top_features=rows[: max(0, int(top_k))],
        warnings=warnings,
        blockers=blockers,
    )
