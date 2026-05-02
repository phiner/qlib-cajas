from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow]


class RunFinalReproducibilityClosureSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "closure"
            subprocess.run([sys.executable, "cajas/scripts/run_final_reproducibility_closure_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "fingerprints" / "run_a_stable_fingerprint.json").exists())
            self.assertTrue((out / "fingerprints" / "run_b_stable_fingerprint.json").exists())
            self.assertTrue((out / "stable_repro" / "stable_reproducibility_report.json").exists())
            self.assertTrue((out / "final" / "final_readiness_packet.json").exists())
            self.assertTrue((out / "bundle" / "final_research_bundle.json").exists())


if __name__ == "__main__":
    unittest.main()
