from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.run_smoke_validation import build_tier_commands


class ValidationRunnersTests(unittest.TestCase):
    def test_fast_validation_uses_exclusion_markers(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn("not smoke and not slow and not closure and not full and not integration", txt)
        self.assertIn("--durations", txt)

    def test_smoke_validation_default_is_micro(self) -> None:
        txt = Path("cajas/scripts/run_smoke_validation.py").read_text(encoding="utf-8")
        self.assertIn('default="micro"', txt)

    def test_micro_tier_does_not_invoke_closure_or_full(self) -> None:
        cmds = build_tier_commands(py="python", out_root=Path("tmp/smoke"), tier="micro")
        joined = "\n".join(" ".join(cmd) for cmd in cmds)
        self.assertNotIn("run_governance_review_closure_smoke.py", joined)
        self.assertNotIn("run_full_research_stack_smoke.py", joined)

    def test_quick_tier_avoids_full_pytest_sweep(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn('"--tier", choices=["quick", "fast", "full-pytest"]', txt)
        self.assertIn("pytest_quick_policy", txt)

    def test_fast_validation_writes_timing_json(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "timing.json"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/run_fast_validation.py",
                    "--tier",
                    "quick",
                    "--timing-json",
                    str(out),
                ],
                check=True,
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["tier"], "quick")
            self.assertIn("total_seconds", payload)

    def test_fail_on_budget_returns_nonzero(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "timing.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/run_fast_validation.py",
                    "--tier",
                    "quick",
                    "--max-seconds",
                    "0",
                    "--fail-on-budget",
                    "--timing-json",
                    str(out),
                ],
            )
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
