"""Build a research-only decision report from phase 35-40 artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ResearchDecisionReport:
    output_dir: str
    decision_summary: list[str]
    recommended_next_phase: str
    trading_profit_backtest_recommendations_present: bool
    files_written: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_research_decision_report(
    *,
    external_run_dir: str | Path,
    output_dir: str | Path,
    run_name: str,
    benchmark_report_path: str | Path | None = None,
    flat_diagnosis_path: str | Path | None = None,
    horizon_train_preview_path: str | Path | None = None,
    horizon_holdout_preview_path: str | Path | None = None,
    feature_group_audit_path: str | Path | None = None,
    write_artifacts: bool = True,
) -> ResearchDecisionReport:
    ext = Path(external_run_dir).expanduser().resolve()
    out_dir = Path(output_dir).expanduser().resolve() / run_name
    if write_artifacts:
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)

    metrics_holdout = _load(ext / "metrics_holdout.json")
    summary = _load(ext / "external_holdout_dataset_summary.json")

    benchmark = _load(Path(benchmark_report_path).expanduser().resolve()) if benchmark_report_path else {}
    flat_diag = _load(Path(flat_diagnosis_path).expanduser().resolve()) if flat_diagnosis_path else {}
    horizon_train = _load(Path(horizon_train_preview_path).expanduser().resolve()) if horizon_train_preview_path else {}
    horizon_holdout = _load(Path(horizon_holdout_preview_path).expanduser().resolve()) if horizon_holdout_preview_path else {}
    feature_audit = _load(Path(feature_group_audit_path).expanduser().resolve()) if feature_group_audit_path else {}

    decision_summary = [
        f"External holdout accuracy={metrics_holdout.get('accuracy')} macro_f1={metrics_holdout.get('macro_f1')}.",
        "Current future_direction_8 is learnable at modest level on 2025 out-of-sample classification.",
        "Flat class appears weak/rare in current definition; redesign is recommended before scaling.",
        "External holdout validation supports further feature/label research, not trading conclusions.",
    ]
    next_phase = "phase41_label_redesign_and_horizon_specific_external_holdout"

    payload = {
        "scope": "classification_research_only",
        "external_holdout_metrics": metrics_holdout,
        "external_holdout_dataset_summary": summary,
        "external_vs_internal_benchmark": benchmark,
        "flat_class_diagnosis": flat_diag,
        "horizon_preview_train": horizon_train,
        "horizon_preview_holdout": horizon_holdout,
        "feature_group_audit": feature_audit,
        "decision_summary": decision_summary,
        "recommended_next_phase": next_phase,
        "forbidden_interpretations": [
            "no buy/sell rules",
            "no trading strategy conclusions",
            "no backtest/profit optimization",
        ],
    }

    md_lines = [
        "# Phase 40 Research Decision Report",
        "",
        "This report is classification research only.",
        "",
        "## Decision Summary",
    ] + [f"- {line}" for line in decision_summary] + [
        "",
        "## Recommended Next Phase",
        f"- {next_phase}",
        "",
        "## Boundaries",
        "- No trading strategy recommendations.",
        "- No backtest/profit conclusions.",
        "- `future_direction_*` labels are research targets only.",
    ]

    files_written: list[str] = []
    if write_artifacts:
        json_path = out_dir / "research_decision_report.json"
        md_path = out_dir / "research_decision_report.md"
        json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
        files_written = [str(md_path), str(json_path)]

    return ResearchDecisionReport(
        output_dir=str(out_dir),
        decision_summary=decision_summary,
        recommended_next_phase=next_phase,
        trading_profit_backtest_recommendations_present=False,
        files_written=files_written,
        warnings=[],
    )
