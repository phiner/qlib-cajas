from __future__ import annotations

import unittest

from cajas.reports.final_readiness_summary import render_final_readiness_summary


class FinalReadinessSummaryTests(unittest.TestCase):
    def test_contains_status_and_blocked(self) -> None:
        md = render_final_readiness_summary(packet={"final_status": "blocked", "gate_summary": {}, "reproducibility_summary": {}, "ci_plan_summary": {}, "manifest_summary": {"missing_artifacts": []}, "blocked_actions": ["no_broker"], "manual_review_checklist": []})
        self.assertIn("final_status", md)
        self.assertIn("Blocked Actions", md)


if __name__ == "__main__":
    unittest.main()
