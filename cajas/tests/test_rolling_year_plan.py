from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.validation.rolling_year_plan import build_rolling_year_validation_plan


class RollingYearPlanTests(unittest.TestCase):
    def test_plan_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = build_rolling_year_validation_plan(output_dir=Path(tmp), run_name="r")
            self.assertEqual(len(rep["rows"]), 4)


if __name__ == "__main__":
    unittest.main()
