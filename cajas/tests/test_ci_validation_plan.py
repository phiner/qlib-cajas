from __future__ import annotations

import unittest

from cajas.reports.ci_validation_plan import build_ci_validation_plan


class CiValidationPlanTests(unittest.TestCase):
    def test_contains_required_commands(self) -> None:
        plan = build_ci_validation_plan()
        merged = "\n".join(cmd for t in plan["tiers"] for cmd in t["commands"])
        self.assertIn("check_path_hygiene.py", merged)
        self.assertIn("not slow and not smoke", merged)
        self.assertIn("run_smoke_validation.py --tier minimal", merged)


if __name__ == "__main__":
    unittest.main()
