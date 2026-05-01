#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_decision_report import build_research_decision_report


def _default_if_exists(path: Path) -> str | None:
    return str(path) if path.exists() else None


def main() -> int:
    p = argparse.ArgumentParser(description="Build phase 40 research decision report.")
    p.add_argument("--external-run-dir", required=True)
    p.add_argument("--output-dir", default="tmp/cajas/research_decision_reports")
    p.add_argument("--run-name", default="phase40_research_decision_report")
    p.add_argument("--benchmark-report-path")
    p.add_argument("--flat-diagnosis-path")
    p.add_argument("--horizon-train-preview-path")
    p.add_argument("--horizon-holdout-preview-path")
    p.add_argument("--feature-group-audit-path")
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    benchmark = args.benchmark_report_path or _default_if_exists(
        Path("tmp/cajas/external_holdout_benchmarks/phase36_external_holdout_benchmark/external_holdout_benchmark_report.json")
    )
    flat_diag = args.flat_diagnosis_path or _default_if_exists(
        Path("tmp/cajas/flat_class_diagnosis/phase37_flat_class_diagnosis/flat_class_diagnosis_report.json")
    )
    horizon_train = args.horizon_train_preview_path or _default_if_exists(
        Path("tmp/cajas/horizon_label_previews/phase38_horizon_preview_train/horizon_label_preview_report.json")
    )
    horizon_holdout = args.horizon_holdout_preview_path or _default_if_exists(
        Path("tmp/cajas/horizon_label_previews/phase38_horizon_preview_holdout/horizon_label_preview_report.json")
    )
    feature_audit = args.feature_group_audit_path or _default_if_exists(
        Path("tmp/cajas/feature_group_audits/phase39_feature_group_audit/feature_group_audit_report.json")
    )

    report = build_research_decision_report(
        external_run_dir=args.external_run_dir,
        output_dir=args.output_dir,
        run_name=args.run_name,
        benchmark_report_path=benchmark,
        flat_diagnosis_path=flat_diag,
        horizon_train_preview_path=horizon_train,
        horizon_holdout_preview_path=horizon_holdout,
        feature_group_audit_path=feature_audit,
        write_artifacts=args.write_artifacts,
    )
    payload = report.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Research decision report completed.")
        print(f"output dir: {payload['output_dir']}")
        print(f"recommended next phase: {payload['recommended_next_phase']}")
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
