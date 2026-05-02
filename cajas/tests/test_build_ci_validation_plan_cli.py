from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from cajas.scripts import build_ci_validation_plan as ci_plan_cli


class BuildCiValidationPlanCliTests(unittest.TestCase):
    def test_cli_writes_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            argv = ["build_ci_validation_plan.py", "--out-dir", str(d)]
            with mock.patch.object(sys, "argv", argv):
                rc = ci_plan_cli.main()
            self.assertEqual(rc, 0)
            self.assertTrue((d / "ci_validation_plan.json").exists())
            self.assertTrue((d / "ci_validation_plan.md").exists())


if __name__ == "__main__":
    unittest.main()
