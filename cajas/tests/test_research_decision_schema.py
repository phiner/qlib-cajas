from __future__ import annotations

import unittest

from cajas.reports.research_decision_schema import ResearchDecisionResult


class ResearchDecisionSchemaTests(unittest.TestCase):
    def test_to_dict_validates_enums(self) -> None:
        result = ResearchDecisionResult(
            run_id="r1",
            created_at_utc="2026-01-01T00:00:00+00:00",
            label_variant_summary_path="a",
            feature_set_summary_path="b",
            calibration_summary_path="c",
            seed_stability_summary_path="d",
            rolling_validation_plan_path="e",
            error_slice_summary_path="f",
            leakage_drift_audit_path="g",
            qlib_readiness_report_path="h",
            final_decision="candidate_for_qlib_trial",
            confidence_level="medium",
        )
        payload = result.to_dict()
        self.assertEqual(payload["run_id"], "r1")


if __name__ == "__main__":
    unittest.main()

