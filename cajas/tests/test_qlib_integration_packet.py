from __future__ import annotations

import unittest

from cajas.reports.qlib_adapter_contract import ContractIssue
from cajas.reports.qlib_integration_packet import build_qlib_integration_packet


class QlibIntegrationPacketTests(unittest.TestCase):
    def test_blocked_when_errors_exist(self) -> None:
        packet = build_qlib_integration_packet(
            contract={"promotion_status": "candidate_for_manual_review"},
            issues=[ContractIssue("error", "x", "y")],
        )
        self.assertEqual(packet["readiness_decision"], "blocked")


if __name__ == "__main__":
    unittest.main()
