from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_research_decision_packet import main


class BuildResearchDecisionPacketCliTests(unittest.TestCase):
    def test_cli_writes_expected_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reports = root / "reports"
            out = root / "out"
            reports.mkdir()
            for name, payload in {
                "label_variant_comparison_report.json": {"run_count": 2},
                "feature_set_comparison_report.json": {"run_count": 2},
                "calibration_analysis_report.json": {"ece_like": 0.01},
                "seed_stability_report.json": {"macro_f1_std": 0.01},
                "rolling_year_validation_plan.json": {"rows": 4},
                "error_slice_analysis_report.json": {"slice_rows": 4},
                "leakage_drift_audit_report.json": {"forbidden_feature_columns_count": 0, "drift_score_max": 0.1},
                "qlib_readiness_report.json": {"unresolved_blockers": []},
            }.items():
                (reports / name).write_text(json.dumps(payload), encoding="utf-8")
            code = main(["--reports-dir", str(reports), "--out-dir", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue((out / "research_decision_packet.json").exists())
            self.assertTrue((out / "research_decision_packet.md").exists())
            self.assertTrue((out / "research_decision_findings.csv").exists())
            self.assertTrue((out / "research_decision_recommendations.csv").exists())


if __name__ == "__main__":
    unittest.main()
