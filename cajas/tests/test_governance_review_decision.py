from __future__ import annotations

import unittest

from cajas.reports.governance_review_decision import build_governance_review_decision


class GovernanceReviewDecisionTests(unittest.TestCase):
    def test_valid_approval(self) -> None:
        rep = build_governance_review_decision(
            governance_remediation_report={"final_suggested_status": "needs_manual_review", "true_violations": []},
            final_readiness_packet={"final_status": "needs_manual_governance_review"},
            stable_reproducibility_report={"final_status": "stable_reproducible"},
            decision={"decision": "approve_offline_research_only"},
        )
        self.assertEqual(rep["governance_review_status"], "offline_research_governance_approved")

    def test_violation_overrides_approval(self) -> None:
        rep = build_governance_review_decision(
            governance_remediation_report={"final_suggested_status": "fail", "true_violations": [{"x": 1}]},
            final_readiness_packet={},
            stable_reproducibility_report={},
            decision={"decision": "approve_offline_research_only"},
        )
        self.assertEqual(rep["governance_review_status"], "blocked")


if __name__ == "__main__":
    unittest.main()

