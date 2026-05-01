"""Build a consolidated research report pack from existing artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from cajas.baseline.confidence_analysis import analyze_prediction_confidence
from cajas.baseline.feature_importance_summary import summarize_feature_importance_across_runs
from cajas.registry.run_health_check import check_run_registry_health
from cajas.reports.markdown_report_exporter import write_markdown_report


@dataclass(frozen=True)
class ResearchReportPack:
    output_dir: str
    title: str
    sections: list[str]
    files_written: list[str]
    warnings: list[str]
    trading_sections_present: bool

    def to_dict(self) -> dict:
        return asdict(self)


def build_research_report_pack(
    *,
    output_dir: str | Path,
    run_name: str,
    title: str,
    registry_path: str | Path,
    baseline_run_dir: str | Path,
    include_dashboard_export: bool = True,
) -> ResearchReportPack:
    out_dir = Path(output_dir).expanduser().resolve() / run_name
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    base = Path(baseline_run_dir).expanduser().resolve()
    metrics_test = json.loads((base / "metrics_test.json").read_text(encoding="utf-8")) if (base / "metrics_test.json").exists() else {}
    metrics_valid = json.loads((base / "metrics_valid.json").read_text(encoding="utf-8")) if (base / "metrics_valid.json").exists() else {}
    metrics_holdout = json.loads((base / "metrics_holdout.json").read_text(encoding="utf-8")) if (base / "metrics_holdout.json").exists() else {}
    meta = json.loads((base / "model_metadata.json").read_text(encoding="utf-8"))

    conf_src = base / "predictions_test.csv"
    conf_split = "test"
    if not conf_src.exists() and (base / "predictions_holdout.csv").exists():
        conf_src = base / "predictions_holdout.csv"
        conf_split = "holdout"
    conf = analyze_prediction_confidence(prediction_csv=conf_src, split=conf_split)
    fi = summarize_feature_importance_across_runs(run_dirs=[base], top_k=20)
    health = check_run_registry_health(registry_path=registry_path)

    sections = [
        "Project scope",
        "Dataset summary",
        "Baseline model summary",
        "Classification metrics",
        "Feature importance summary",
        "Confidence analysis summary",
        "Registry health summary",
        "Boundaries and forbidden interpretations",
    ]

    summary_text = (
        f"Model family: `{meta.get('model_family_used')}`\n\n"
        f"Target label: `{meta.get('target_label')}`\n\n"
        f"Valid accuracy: `{metrics_valid.get('accuracy')}`\n\n"
        f"Test accuracy: `{metrics_test.get('accuracy')}`\n\n"
        f"Holdout accuracy: `{metrics_holdout.get('accuracy')}`\n\n"
        f"Confidence buckets: `{len(conf.buckets)}`\n\n"
        f"Feature summary count: `{len(fi.features)}`\n\n"
        f"Registry health errors: `{health.error_count}`\n\n"
        "No trading strategy, no backtest, no profit analysis. Predictions are classification outputs only."
    )

    md_path = write_markdown_report(
        output_path=out_dir / "research_report.md",
        title=title,
        sections=[("Summary", summary_text)],
    )

    pack_payload = {
        "title": title,
        "sections": sections,
        "baseline": {"metrics_valid": metrics_valid, "metrics_test": metrics_test, "metrics_holdout": metrics_holdout, "model_metadata": meta},
        "feature_importance": fi.to_dict(),
        "confidence": conf.to_dict(),
        "registry_health": health.to_dict(),
        "include_dashboard_export": include_dashboard_export,
    }

    (out_dir / "research_report_pack.json").write_text(json.dumps(pack_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "title": title,
        "files": ["research_report.md", "research_report_pack.json"],
        "trading_sections_present": False,
    }
    (out_dir / "research_report_manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return ResearchReportPack(
        output_dir=str(out_dir),
        title=title,
        sections=sections,
        files_written=[str(md_path), str(out_dir / "research_report_pack.json"), str(out_dir / "research_report_manifest.json")],
        warnings=[],
        trading_sections_present=False,
    )
