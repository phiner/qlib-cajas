from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunResearchPacketSmokeTests(unittest.TestCase):
    def test_smoke_produces_key_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_research_packet_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "decision" / "research_decision_packet.json").exists())
            self.assertTrue((out / "promotion" / "candidate_promotion_manifest.json").exists())
            self.assertTrue((out / "index" / "research_report_index.json").exists())


if __name__ == "__main__":
    unittest.main()

