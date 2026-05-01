from __future__ import annotations

import unittest

from cajas.reports.research_gate_summary import render_research_gate_summary


class ResearchGateSummaryTests(unittest.TestCase):
    def test_contains_final_status(self) -> None:
        md = render_research_gate_summary(
            gate_packet={"final_status": "blocked", "checks": [], "artifact_checks": [], "metric_summary": {}, "manual_review_checklist": []},
            no_broker_packet={"next_blocked_actions": [{"action": "no_trade", "reason": "blocked"}]},
        )
        self.assertIn("final_status", md)


if __name__ == "__main__":
    unittest.main()
