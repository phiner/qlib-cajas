"""Build a consolidated baseline report pack from an existing run."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

import pandas as pd

from cajas.baseline.baseline_artifact_inspector import inspect_baseline_run_artifacts
from cajas.baseline.feature_importance_inspector import inspect_feature_importance
from cajas.baseline.prediction_review import build_prediction_review


@dataclass(frozen=True)
class BaselineReportPack:
    run_dir: str
    run_name: str
    model_family: str | None
    target_label: str | None
    feature_count: int | None
    valid_metrics: dict
    test_metrics: dict
    prediction_review: dict
    feature_importance: dict
    artifact_inspection: dict
    trading_metrics_present: bool
    warnings: list[str]
    blockers: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_baseline_report_pack(
    *,
    run_dir: str | Path,
    output_dir: str | Path,
    run_name: str,
    write_artifacts: bool = True,
    top_k_features: int = 30,
) -> BaselineReportPack:
    base_run = Path(run_dir).expanduser().resolve()
    out_root = Path(output_dir).expanduser().resolve()
    out_dir = out_root / run_name
    if write_artifacts:
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)

    inspect = inspect_baseline_run_artifacts(base_run)
    valid_review = build_prediction_review(
        prediction_csv=base_run / "predictions_valid.csv",
        output_dir=out_dir if write_artifacts else Path("/tmp"),
        split="valid",
    )
    test_review = build_prediction_review(
        prediction_csv=base_run / "predictions_test.csv",
        output_dir=out_dir if write_artifacts else Path("/tmp"),
        split="test",
    )
    fi = inspect_feature_importance(run_dir=base_run, top_k=top_k_features)

    pack = BaselineReportPack(
        run_dir=str(base_run),
        run_name=run_name,
        model_family=inspect.model_family_used,
        target_label=inspect.target_label,
        feature_count=inspect.feature_count,
        valid_metrics=inspect.metrics_valid,
        test_metrics=inspect.metrics_test,
        prediction_review={"valid": valid_review.to_dict(), "test": test_review.to_dict()},
        feature_importance=fi.to_dict(),
        artifact_inspection=inspect.to_dict(),
        trading_metrics_present=False,
        warnings=list(dict.fromkeys(inspect.warnings + fi.warnings + valid_review.warnings + test_review.warnings)),
        blockers=list(dict.fromkeys([i.message for i in inspect.issues if i.severity == "error"] + fi.blockers)),
    )

    if write_artifacts:
        _write_json(out_dir / "baseline_report_pack.json", pack.to_dict())
        _write_json(out_dir / "metrics_summary.json", {"valid": inspect.metrics_valid, "test": inspect.metrics_test})
        _write_json(out_dir / "feature_importance_summary.json", fi.to_dict())
        _write_json(out_dir / "prediction_review_summary.json", pack.prediction_review)
        _write_json(out_dir / "artifact_inspection_summary.json", inspect.to_dict())
        if fi.top_features:
            pd.DataFrame(fi.top_features).to_csv(out_dir / "top_feature_importance.csv", index=False)

    return pack
