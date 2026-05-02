from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


FIXTURE_DIR = Path("cajas/data_examples/validation_fixtures")


class ValidationFixturesTests(unittest.TestCase):
    def test_fixture_files_are_valid_json(self) -> None:
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)

    def test_fixture_builders_consume_tiny_inputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision_json = root / "governance_review_decision.json"
            decision_md = root / "governance_review_decision.md"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_governance_review_decision.py",
                    "--governance-remediation-report",
                    str(FIXTURE_DIR / "governance_remediation_needs_manual_review.json"),
                    "--final-readiness-packet",
                    str(FIXTURE_DIR / "final_readiness_needs_manual_governance_review.json"),
                    "--stable-reproducibility-report",
                    str(FIXTURE_DIR / "stable_reproducibility_report_pass.json"),
                    "--decision",
                    str(FIXTURE_DIR / "governance_review_decision_approve_offline_only.json"),
                    "--out-json",
                    str(decision_json),
                    "--out-md",
                    str(decision_md),
                ],
                check=True,
            )
            self.assertTrue(decision_json.exists())


if __name__ == "__main__":
    unittest.main()
