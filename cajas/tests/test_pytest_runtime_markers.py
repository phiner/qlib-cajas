from __future__ import annotations

import unittest
from pathlib import Path


class PytestRuntimeMarkersTests(unittest.TestCase):
    def test_pytest_markers_declared(self) -> None:
        txt = Path("pytest.ini").read_text(encoding="utf-8")
        self.assertIn("smoke:", txt)
        self.assertIn("slow:", txt)
        self.assertIn("closure:", txt)
        self.assertIn("full:", txt)

    def test_closure_and_full_smokes_marked(self) -> None:
        closure_target = Path("cajas/tests/test_run_governance_review_closure_smoke.py").read_text(encoding="utf-8")
        full_target = Path("cajas/tests/test_run_full_research_stack_smoke.py").read_text(encoding="utf-8")
        self.assertIn("pytest.mark.closure", closure_target)
        self.assertIn("pytest.mark.full", full_target)

    def test_readme_mentions_fast_command(self) -> None:
        readme = Path("cajas/README.md").read_text(encoding="utf-8")
        self.assertIn("run_fast_validation.py", readme)


if __name__ == "__main__":
    unittest.main()
