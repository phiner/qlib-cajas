from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_decision_builder import build_research_decision


class ResearchDecisionBuilderTests(unittest.TestCase):
    def test_candidate_path_without_blockers(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "label_variant_comparison_report.json").write_text(json.dumps({"run_count": 2}), encoding="utf-8")
            (d / "feature_set_comparison_report.json").write_text(json.dumps({"run_count": 2}), encoding="utf-8")
            (d / "calibration_analysis_report.json").write_text(json.dumps({"ece_like": 0.01}), encoding="utf-8")
            (d / "seed_stability_report.json").write_text(json.dumps({"macro_f1_std": 0.01}), encoding="utf-8")
            (d / "rolling_year_validation_plan.json").write_text(json.dumps({"rows": 4}), encoding="utf-8")
            (d / "error_slice_analysis_report.json").write_text(json.dumps({"slice_rows": 3}), encoding="utf-8")
            (d / "leakage_drift_audit_report.json").write_text(
                json.dumps({"forbidden_feature_columns_count": 0, "drift_score_max": 0.1}), encoding="utf-8"
            )
            (d / "qlib_readiness_report.json").write_text(json.dumps({"unresolved_blockers": []}), encoding="utf-8")
            res = build_research_decision(reports_dir=d, run_id="smoke")
            self.assertEqual(res.final_decision, "candidate_for_qlib_trial")

    def test_missing_required_file_is_blocking(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            res = build_research_decision(reports_dir=d, run_id="smoke")
            self.assertTrue(res.blocking_findings)
            self.assertEqual(res.final_decision, "reject")


if __name__ == "__main__":
    unittest.main()

