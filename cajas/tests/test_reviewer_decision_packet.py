from __future__ import annotations

import unittest

from cajas.reports.reviewer_decision_packet import build_reviewer_decision_packet


class ReviewerDecisionPacketTests(unittest.TestCase):
    def test_accepts_valid_decision(self) -> None:
        packet = build_reviewer_decision_packet(
            decision={"decision": "research_review_approved", "accepted_risks": ["r1"], "rejected_actions": ["live trading"]},
            final_readiness_packet={"final_status": "research_stack_ready_for_manual_review"},
        )
        self.assertEqual(packet["decision"], "research_review_approved")
        self.assertIn("live trading", packet["rejected_actions"])

    def test_rejects_invalid_decision(self) -> None:
        with self.assertRaises(ValueError):
            build_reviewer_decision_packet(decision={"decision": "ok"}, final_readiness_packet={})


if __name__ == "__main__":
    unittest.main()

