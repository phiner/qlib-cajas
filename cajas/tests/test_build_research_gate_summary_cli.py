from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildResearchGateSummaryCliTests(unittest.TestCase):
    def test_cli_writes_md(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            gate = d / "gate.json"
            nb = d / "nb.json"
            gate.write_text(json.dumps({"final_status": "blocked", "checks": [], "artifact_checks": [], "metric_summary": {}, "manual_review_checklist": []}), encoding="utf-8")
            nb.write_text(json.dumps({"next_blocked_actions": []}), encoding="utf-8")
            out = d / "summary.md"
            subprocess.run([
                sys.executable, "cajas/scripts/build_research_gate_summary.py", "--gate-packet", str(gate), "--no-broker-packet", str(nb), "--out", str(out)
            ], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
