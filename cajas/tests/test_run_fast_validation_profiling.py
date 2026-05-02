from __future__ import annotations

import argparse
import unittest

from cajas.scripts.run_fast_validation import _build_steps, _build_pytest_cmd


class RunFastValidationProfilingTests(unittest.TestCase):
    def _ns(self, **kwargs) -> argparse.Namespace:
        base = {
            "tier": "fast",
            "skip_compileall": False,
            "skip_pytest": False,
            "only_pytest": False,
            "only_hygiene": False,
            "durations": None,
            "pytest_extra_args": None,
            "pytest_expression": "not smoke and not slow and not closure and not full and not integration",
        }
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_only_pytest_runs_single_step(self) -> None:
        steps = _build_steps(self._ns(only_pytest=True), "python")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0][0], "pytest_fast")

    def test_skip_pytest_omits_pytest_step(self) -> None:
        steps = _build_steps(self._ns(skip_pytest=True), "python")
        names = [x[0] for x in steps]
        self.assertNotIn("pytest_fast", names)

    def test_quick_tier_avoids_full_pytest(self) -> None:
        steps = _build_steps(self._ns(tier="quick"), "python")
        names = [x[0] for x in steps]
        self.assertIn("pytest_quick_policy", names)
        self.assertNotIn("pytest_full", names)

    def test_pytest_cmd_includes_durations(self) -> None:
        cmd = _build_pytest_cmd("python", "x", 30, None)
        self.assertIn("--durations=30", cmd)


if __name__ == "__main__":
    unittest.main()
