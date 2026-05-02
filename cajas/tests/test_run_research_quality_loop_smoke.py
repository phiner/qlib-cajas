from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunResearchQualityLoopSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "quality"
            subprocess.run([sys.executable, "cajas/scripts/run_research_quality_loop_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "repro_explain" / "stable_reproducibility_explanation.json").exists())
            self.assertTrue((out / "normalization" / "normalization_coverage_report.json").exists())
            self.assertTrue((out / "governance" / "governance_remediation_report.json").exists())
            self.assertTrue((out / "final" / "final_readiness_packet.json").exists())
            self.assertTrue((out / "reviewer" / "reviewer_decision_packet.json").exists())
            self.assertTrue((out / "bundle" / "final_research_bundle.json").exists())


if __name__ == "__main__":
    unittest.main()

