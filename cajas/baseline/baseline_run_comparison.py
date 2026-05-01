"""Compare baseline run artifacts by classification metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class BaselineRunComparisonReport:
    run_dirs: list[str]
    primary_metric: str
    rows: list[dict]
    best_run: str | None
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def compare_baseline_runs(*, run_dirs: list[str | Path], primary_metric: str = "test_macro_f1") -> BaselineRunComparisonReport:
    rows: list[dict] = []
    warnings: list[str] = []

    for run_dir in run_dirs:
        base = Path(run_dir).expanduser().resolve()
        mt = base / "metrics_test.json"
        mv = base / "metrics_valid.json"
        mm = base / "model_metadata.json"
        if not (mt.exists() and mv.exists() and mm.exists()):
            warnings.append(f"Missing artifacts for comparison in {base}")
            continue
        test_metrics = json.loads(mt.read_text(encoding="utf-8"))
        valid_metrics = json.loads(mv.read_text(encoding="utf-8"))
        meta = json.loads(mm.read_text(encoding="utf-8"))
        rows.append(
            {
                "run_dir": str(base),
                "run_name": base.name,
                "model_family": meta.get("model_family_used"),
                "test_accuracy": float(test_metrics.get("accuracy", 0.0)),
                "test_macro_f1": float(test_metrics.get("macro_f1", 0.0)),
                "test_weighted_f1": float(test_metrics.get("weighted_f1", 0.0)),
                "valid_accuracy": float(valid_metrics.get("accuracy", 0.0)),
                "valid_macro_f1": float(valid_metrics.get("macro_f1", 0.0)),
                "valid_weighted_f1": float(valid_metrics.get("weighted_f1", 0.0)),
            }
        )

    best_run = None
    if rows:
        rows.sort(key=lambda x: x.get(primary_metric, 0.0), reverse=True)
        best_run = rows[0]["run_name"]

    return BaselineRunComparisonReport(
        run_dirs=[str(Path(p).expanduser().resolve()) for p in run_dirs],
        primary_metric=primary_metric,
        rows=rows,
        best_run=best_run,
        warnings=warnings,
    )
