from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildNoBrokerDryRunPacketCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            gate = d / "gate.json"
            gate.write_text(json.dumps({"final_status": "blocked", "source_artifact_paths": {}, "metric_summary": {}, "manual_review_checklist": [], "blocked_actions": []}), encoding="utf-8")
            out = d / "no_broker.json"
            subprocess.run([
                sys.executable, "cajas/scripts/build_no_broker_dry_run_packet.py", "--gate-packet", str(gate), "--out", str(out)
            ], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
