from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class RunSmokeValidationTiersTests(unittest.TestCase):
    def test_micro_tier_creates_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "smoke"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/run_smoke_validation.py",
                    "--tier",
                    "micro",
                    "--out-root",
                    str(out_root),
                ],
                check=True,
            )
            self.assertTrue((out_root / "micro" / "ci_plan" / "ci_validation_plan.json").exists())
            self.assertTrue((out_root / "micro" / "runtime_audit" / "validation_runtime_audit.json").exists())
            self.assertTrue((out_root / "micro" / "approval" / "research_only_approval_packet.json").exists())


if __name__ == "__main__":
    unittest.main()
