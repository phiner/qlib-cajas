from __future__ import annotations

import unittest
from pathlib import Path


class PytestRuntimeMarkersTests(unittest.TestCase):
    def test_pytest_markers_declared(self) -> None:
        txt = Path("pytest.ini").read_text(encoding="utf-8")
        self.assertIn("smoke:", txt)
        self.assertIn("slow:", txt)

    def test_heavy_smoke_tests_marked(self) -> None:
        target = Path("cajas/tests/test_run_governance_review_closure_smoke.py").read_text(encoding="utf-8")
        self.assertIn("pytestmark = [pytest.mark.smoke, pytest.mark.slow]", target)

    def test_readme_mentions_fast_command(self) -> None:
        readme = Path("cajas/README.md").read_text(encoding="utf-8")
        self.assertIn('pytest cajas/tests -m "not slow and not smoke"', readme)


if __name__ == "__main__":
    unittest.main()
