from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunResearchGateSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_research_gate_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "gate" / "research_gate_packet.json").exists())
            self.assertTrue((out / "no_broker" / "no_broker_dry_run_packet.json").exists())
            self.assertTrue((out / "summary" / "research_gate_summary.md").exists())


if __name__ == "__main__":
    unittest.main()
