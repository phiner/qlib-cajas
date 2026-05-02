from __future__ import annotations

import glob
import unittest
from pathlib import Path


ALLOWLIST_NO_MARKER = {
    "cajas/tests/test_run_smoke_validation_tiers.py",
}


class ValidationMarkerPolicyTests(unittest.TestCase):
    def test_pytest_ini_defines_required_markers(self) -> None:
        txt = Path("pytest.ini").read_text(encoding="utf-8")
        for marker in ["unit:", "integration:", "smoke:", "slow:", "closure:", "full:"]:
            self.assertIn(marker, txt)

    def test_run_smoke_files_have_smoke_and_slow(self) -> None:
        for path in sorted(glob.glob("cajas/tests/test_run_*_smoke.py")):
            if path in ALLOWLIST_NO_MARKER:
                continue
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn("pytest.mark.smoke", text)
            self.assertIn("pytest.mark.slow", text)

    def test_full_and_closure_classification_present(self) -> None:
        full_text = Path("cajas/tests/test_run_full_research_stack_smoke.py").read_text(encoding="utf-8")
        closure_text = Path("cajas/tests/test_run_governance_review_closure_smoke.py").read_text(encoding="utf-8")
        self.assertIn("pytest.mark.full", full_text)
        self.assertIn("pytest.mark.closure", closure_text)

    def test_fast_validation_excludes_heavy_markers(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn("not smoke and not slow and not closure and not full and not integration", txt)

    def test_validation_runner_subprocess_tests_must_be_integration(self) -> None:
        text = Path("cajas/tests/test_validation_runners.py").read_text(encoding="utf-8")
        token = "subprocess" + ".run("
        self.assertNotIn(token, text)

    def test_future_training_skeleton_is_not_fast_default(self) -> None:
        text = Path("cajas/tests/test_future_training_skeleton.py").read_text(encoding="utf-8")
        self.assertIn("pytest.mark.slow", text)
        self.assertIn("pytest.mark.integration", text)

    def test_docs_mention_fast_command(self) -> None:
        txt = Path("cajas/README.md").read_text(encoding="utf-8")
        self.assertIn("run_fast_validation.py", txt)


if __name__ == "__main__":
    unittest.main()
