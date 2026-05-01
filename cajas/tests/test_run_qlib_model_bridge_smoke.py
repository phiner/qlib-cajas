from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunQlibModelBridgeSmokeTests(unittest.TestCase):
    def test_smoke(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_qlib_model_bridge_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "contract" / "qlib_model_training_contract.json").exists())
            self.assertTrue((out / "experiment" / "metrics.json").exists())
            self.assertTrue((out / "registry" / "model_run_registry.jsonl").exists())
            self.assertTrue((out / "comparison" / "model_run_comparison.json").exists())


if __name__ == "__main__":
    unittest.main()
