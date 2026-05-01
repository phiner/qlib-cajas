from __future__ import annotations

import unittest

from cajas.reports.research_gate_schema import ResearchGatePacket


class ResearchGateSchemaTests(unittest.TestCase):
    def test_to_dict(self) -> None:
        p = ResearchGatePacket(
            schema_version="v1",
            source_artifact_paths={},
            artifact_checks=[],
            metric_summary={},
            checks=[],
            manual_review_checklist=[],
            blocked_actions=[],
            final_status="blocked",
        )
        self.assertEqual(p.to_dict()["final_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
