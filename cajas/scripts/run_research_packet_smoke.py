#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run lightweight end-to-end research packet smoke workflow.")
    p.add_argument("--out-root", default="tmp/research-packet-smoke")
    args = p.parse_args()
    out_root = Path(args.out_root).expanduser().resolve()
    reports_dir = out_root / "reports"
    decision_dir = out_root / "decision"
    promotion_dir = out_root / "promotion"
    index_dir = out_root / "index"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _write_json(reports_dir / "label_variant_comparison_report.json", {"run_count": 2, "best_run_name": "demo_label"})
    _write_json(reports_dir / "feature_set_comparison_report.json", {"run_count": 2, "best_feature_set": "structure_v1"})
    _write_json(reports_dir / "calibration_analysis_report.json", {"ece_like": 0.03})
    _write_json(reports_dir / "seed_stability_report.json", {"macro_f1_std": 0.01, "macro_f1_mean": 0.34})
    _write_json(reports_dir / "rolling_year_validation_plan.json", {"rows": 4})
    _write_json(reports_dir / "error_slice_analysis_report.json", {"slice_rows": 3})
    _write_json(reports_dir / "leakage_drift_audit_report.json", {"forbidden_feature_columns_count": 0, "drift_score_max": 0.1})
    _write_json(reports_dir / "qlib_readiness_report.json", {"unresolved_blockers": []})

    py = sys.executable
    _run([py, "cajas/scripts/build_research_decision_packet.py", "--reports-dir", str(reports_dir), "--out-dir", str(decision_dir), "--run-id", "phase62_smoke"])
    _run(
        [
            py,
            "cajas/scripts/build_candidate_promotion_manifest.py",
            "--decision-packet",
            str(decision_dir / "research_decision_packet.json"),
            "--out-dir",
            str(promotion_dir),
            "--label-variant-id",
            "label_h8_binary_drop_flat",
            "--feature-set-id",
            "structure_v1",
            "--target-name",
            "future_direction_8",
            "--horizon",
            "8",
            "--model-family",
            "LightGBM",
        ]
    )
    _run([py, "cajas/scripts/build_research_report_index.py", "--root-dir", str(out_root), "--out-dir", str(index_dir)])

    print("Research packet smoke completed.")
    print(f"reports_dir: {reports_dir}")
    print(f"decision_dir: {decision_dir}")
    print(f"promotion_dir: {promotion_dir}")
    print(f"index_dir: {index_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

