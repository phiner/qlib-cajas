"""Aggregate feature importance across baseline runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from cajas.baseline.feature_importance_inspector import inspect_feature_importance


@dataclass(frozen=True)
class AggregatedFeatureImportanceItem:
    feature: str
    run_count: int
    mean_importance: float
    mean_rank: float
    max_importance: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FeatureImportanceSummaryReport:
    run_count: int
    features: list[AggregatedFeatureImportanceItem]
    warnings: list[str]
    blockers: list[str]
    trading_logic_present: bool

    def to_dict(self) -> dict:
        return {
            "run_count": self.run_count,
            "features": [x.to_dict() for x in self.features],
            "warnings": self.warnings,
            "blockers": self.blockers,
            "trading_logic_present": self.trading_logic_present,
        }


def summarize_feature_importance_across_runs(
    *,
    run_dirs: list[str | Path],
    top_k: int = 50,
) -> FeatureImportanceSummaryReport:
    acc: dict[str, dict] = {}
    warnings: list[str] = []
    blockers: list[str] = []
    used = 0

    for run_dir in run_dirs:
        rep = inspect_feature_importance(run_dir=run_dir, top_k=100000)
        warnings.extend(rep.warnings)
        blockers.extend(rep.blockers)
        if not rep.available:
            continue
        used += 1
        for row in rep.feature_importance:
            item = acc.setdefault(row["feature"], {"importance": [], "rank": []})
            item["importance"].append(float(row.get("importance", 0.0)))
            item["rank"].append(float(row.get("rank", 0.0)))

    items: list[AggregatedFeatureImportanceItem] = []
    for feature, payload in acc.items():
        vals = payload["importance"]
        ranks = payload["rank"]
        items.append(
            AggregatedFeatureImportanceItem(
                feature=feature,
                run_count=len(vals),
                mean_importance=float(sum(vals) / len(vals)),
                mean_rank=float(sum(ranks) / len(ranks)),
                max_importance=float(max(vals)),
            )
        )

    items.sort(key=lambda x: x.mean_importance, reverse=True)
    return FeatureImportanceSummaryReport(
        run_count=used,
        features=items[: max(0, int(top_k))],
        warnings=list(dict.fromkeys(warnings)),
        blockers=list(dict.fromkeys(blockers)),
        trading_logic_present=False,
    )
