from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow, pytest.mark.closure]


class RunGovernanceReviewClosureSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "gov"
            subprocess.run([sys.executable, "cajas/scripts/run_governance_review_closure_smoke.py", "--out-root", str(out)], check=True)
            self.assertTrue((out / "governance_review" / "governance_review_decision.json").exists())
            self.assertTrue((out / "approval" / "research_only_approval_packet.json").exists())
            self.assertTrue((out / "final" / "final_readiness_packet.json").exists())
            self.assertTrue((out / "bundle" / "final_research_bundle.json").exists())


if __name__ == "__main__":
    unittest.main()
