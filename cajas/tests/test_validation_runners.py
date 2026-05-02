from __future__ import annotations

import unittest
from pathlib import Path


class ValidationRunnersTests(unittest.TestCase):
    def test_fast_validation_uses_exclusion_marker(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn('pytest", "cajas/tests", "-m", "not slow and not smoke"', txt)

    def test_smoke_validation_default_minimal(self) -> None:
        txt = Path("cajas/scripts/run_smoke_validation.py").read_text(encoding="utf-8")
        self.assertIn('default="minimal"', txt)
        self.assertIn("run_governance_review_closure_smoke.py", txt)


if __name__ == "__main__":
    unittest.main()
