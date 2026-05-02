from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow]


class RunFinalReadinessSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_final_readiness_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "manifests" / "run_a_manifest.json").exists())
            self.assertTrue((out / "manifests" / "run_b_manifest.json").exists())
            self.assertTrue((out / "repro" / "reproducibility_report.json").exists())
            self.assertTrue((out / "ci" / "ci_validation_plan.json").exists())
            self.assertTrue((out / "final" / "final_readiness_packet.json").exists())
            self.assertTrue((out / "final" / "final_readiness_summary.md").exists())


if __name__ == "__main__":
    unittest.main()
