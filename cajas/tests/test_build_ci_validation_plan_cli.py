from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildCiValidationPlanCliTests(unittest.TestCase):
    def test_cli_writes_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            subprocess.run([sys.executable, "cajas/scripts/build_ci_validation_plan.py", "--out-dir", str(d)], check=True)
            self.assertTrue((d / "ci_validation_plan.json").exists())
            self.assertTrue((d / "ci_validation_plan.md").exists())


if __name__ == "__main__":
    unittest.main()
