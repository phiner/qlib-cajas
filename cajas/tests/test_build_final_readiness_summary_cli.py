from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_final_readiness_summary import main


class BuildFinalReadinessSummaryCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            packet = d / "packet.json"
            packet.write_text(json.dumps({"final_status": "blocked", "gate_summary": {}, "reproducibility_summary": {}, "ci_plan_summary": {}, "manifest_summary": {"missing_artifacts": []}, "blocked_actions": [], "manual_review_checklist": []}), encoding="utf-8")
            out = d / "summary.md"
            code = main(["--packet", str(packet), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
