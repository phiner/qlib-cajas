"""Benchmark internal split runs against external holdout runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkRunSummary:
    run_name: str
    run_dir: str
    run_kind: str
    model_family: str | None
    target_label: str | None
    accuracy: float | None
    macro_f1: float | None
    weighted_f1: float | None
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ExternalHoldoutBenchmarkReport:
    run_count: int
    external_holdout_count: int
    internal_split_count: int
    summaries: list[BenchmarkRunSummary]
    best_external_holdout_by_macro_f1: str | None
    warnings: list[str]
    trading_metrics_present: bool

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["summaries"] = [s.to_dict() for s in self.summaries]
        return payload


def _safe_load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_external_holdout_benchmark(
    *,
    run_dirs: list[str | Path],
) -> ExternalHoldoutBenchmarkReport:
    summaries: list[BenchmarkRunSummary] = []
    warnings: list[str] = []

    for run_dir in run_dirs:
        base = Path(run_dir).expanduser().resolve()
        if not base.exists():
            warnings.append(f"run directory not found: {base}")
            continue
        mm = base / "model_metadata.json"
        meta = _safe_load_json(mm) if mm.exists() else {}
        mh = base / "metrics_holdout.json"
        mt = base / "metrics_test.json"
        mv = base / "metrics_valid.json"

        notes: list[str] = []
        run_kind = "unknown"
        metrics: dict = {}
        if mh.exists():
            run_kind = "external_holdout"
            metrics = _safe_load_json(mh)
        elif mt.exists() and mv.exists():
            run_kind = "internal_split"
            metrics = _safe_load_json(mt)
        else:
            notes.append("missing expected metric artifacts")
            warnings.append(f"unable to classify run kind for {base}")

        summaries.append(
            BenchmarkRunSummary(
                run_name=base.name,
                run_dir=str(base),
                run_kind=run_kind,
                model_family=meta.get("model_family_used"),
                target_label=meta.get("target_label"),
                accuracy=float(metrics["accuracy"]) if "accuracy" in metrics else None,
                macro_f1=float(metrics["macro_f1"]) if "macro_f1" in metrics else None,
                weighted_f1=float(metrics["weighted_f1"]) if "weighted_f1" in metrics else None,
                notes=notes,
            )
        )

    external = [s for s in summaries if s.run_kind == "external_holdout"]
    internal = [s for s in summaries if s.run_kind == "internal_split"]
    best_external = None
    if external:
        ranked = sorted(external, key=lambda s: s.macro_f1 if s.macro_f1 is not None else float("-inf"), reverse=True)
        best_external = ranked[0].run_name

    return ExternalHoldoutBenchmarkReport(
        run_count=len(summaries),
        external_holdout_count=len(external),
        internal_split_count=len(internal),
        summaries=summaries,
        best_external_holdout_by_macro_f1=best_external,
        warnings=warnings,
        trading_metrics_present=False,
    )
