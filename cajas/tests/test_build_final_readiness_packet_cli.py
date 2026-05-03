from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_final_readiness_packet import main


class BuildFinalReadinessPacketCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            gate = d / "gate.json"
            nb = d / "nb.json"
            man = d / "man.json"
            rep = d / "rep.json"
            ci = d / "ci.json"
            gate.write_text(json.dumps({"final_status": "blocked", "metric_summary": {}, "manual_review_checklist": []}), encoding="utf-8")
            nb.write_text(json.dumps({"disabled_capabilities": ["no_broker"], "next_blocked_actions": ["no_broker"]}), encoding="utf-8")
            man.write_text(json.dumps({"missing_artifact_paths": [], "artifact_inventory": [], "root": str(d)}), encoding="utf-8")
            rep.write_text(json.dumps({"final_status": "reproducible", "warnings": []}), encoding="utf-8")
            ci.write_text(json.dumps({"tiers": []}), encoding="utf-8")
            out = d / "final.json"
            code = main([
                "--gate-packet", str(gate),
                "--no-broker-packet", str(nb),
                "--manifest", str(man),
                "--reproducibility-report", str(rep),
                "--ci-plan", str(ci),
                "--out", str(out),
            ])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
