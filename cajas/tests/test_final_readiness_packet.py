from __future__ import annotations

import unittest

from cajas.reports.final_readiness_packet import build_final_readiness_packet


class FinalReadinessPacketTests(unittest.TestCase):
    def test_preserves_blocked_boundaries(self) -> None:
        packet = build_final_readiness_packet(
            gate_packet={"final_status": "blocked", "metric_summary": {}, "manual_review_checklist": []},
            no_broker_packet={"disabled_capabilities": ["no_broker"], "next_blocked_actions": ["no_broker"]},
            manifest={"missing_artifact_paths": [], "artifact_inventory": []},
            reproducibility_report={"final_status": "reproducible", "warnings": []},
            ci_plan={"tiers": []},
        )
        self.assertEqual(packet["final_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
