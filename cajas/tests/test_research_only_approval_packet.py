from __future__ import annotations

import unittest

from cajas.reports.research_only_approval_packet import build_research_only_approval_packet


class ResearchOnlyApprovalPacketTests(unittest.TestCase):
    def test_approved_scope(self) -> None:
        rep = build_research_only_approval_packet(
            final_readiness_packet={"final_status": "needs_manual_governance_review"},
            stable_reproducibility_report={"final_status": "stable_reproducible"},
            governance_remediation_report={"final_suggested_status": "needs_manual_review"},
            governance_review_decision={"decision": "approve_offline_research_only", "governance_review_status": "offline_research_governance_approved", "true_execution_violation_count": 0},
            offline_review_packet={"overall_review_state": "ready_for_human_review"},
            final_research_bundle={"bundle_status": "ready_for_human_review"},
        )
        self.assertEqual(rep["approval_status"], "offline_research_approved")
        self.assertEqual(rep["approved_scope"], "offline_research_only")
        self.assertIn("broker integration", rep["explicitly_forbidden_scope"])


if __name__ == "__main__":
    unittest.main()

