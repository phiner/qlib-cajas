from __future__ import annotations

import unittest

from cajas.reports.no_broker_dry_run_packet import build_no_broker_dry_run_packet


class NoBrokerDryRunPacketTests(unittest.TestCase):
    def test_blocks_execution_capabilities(self) -> None:
        packet = build_no_broker_dry_run_packet(gate_packet={"final_status": "blocked"})
        self.assertIn("no_broker", packet["disabled_capabilities"])


if __name__ == "__main__":
    unittest.main()
