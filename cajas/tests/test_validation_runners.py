from __future__ import annotations

import unittest
from pathlib import Path

from cajas.scripts.run_smoke_validation import build_tier_commands


class ValidationRunnersTests(unittest.TestCase):
    def test_fast_validation_uses_exclusion_markers(self) -> None:
        txt = Path("cajas/scripts/run_fast_validation.py").read_text(encoding="utf-8")
        self.assertIn("not smoke and not slow and not closure and not full", txt)
        self.assertIn("--durations", txt)

    def test_smoke_validation_default_is_micro(self) -> None:
        txt = Path("cajas/scripts/run_smoke_validation.py").read_text(encoding="utf-8")
        self.assertIn('default="micro"', txt)

    def test_micro_tier_does_not_invoke_closure_or_full(self) -> None:
        cmds = build_tier_commands(py="python", out_root=Path("tmp/smoke"), tier="micro")
        joined = "\n".join(" ".join(cmd) for cmd in cmds)
        self.assertNotIn("run_governance_review_closure_smoke.py", joined)
        self.assertNotIn("run_full_research_stack_smoke.py", joined)

    def test_minimal_tier_avoids_historical_mega_smokes(self) -> None:
        cmds = build_tier_commands(py="python", out_root=Path("tmp/smoke"), tier="minimal")
        joined = "\n".join(" ".join(cmd) for cmd in cmds)
        self.assertNotIn("run_full_research_stack_smoke.py", joined)
        self.assertNotIn("run_research_remediation_smoke.py", joined)


if __name__ == "__main__":
    unittest.main()
