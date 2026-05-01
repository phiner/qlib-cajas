from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunQlibDatasetHandlerSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "smoke"
            subprocess.run([sys.executable, "cajas/scripts/run_qlib_dataset_handler_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "dataset_contract" / "qlib_dataset_contract.json").exists())
            self.assertTrue((out / "handler_input" / "handler_input.csv").exists())
            self.assertTrue((out / "validation" / "qlib_handler_smoke_report.json").exists())


if __name__ == "__main__":
    unittest.main()
