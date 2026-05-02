from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_runtime_audit import build_validation_runtime_audit


class ValidationRuntimeAuditTests(unittest.TestCase):
    def test_static_audit_detects_smoke_tests(self) -> None:
        report = build_validation_runtime_audit(tests_root="cajas/tests")
        self.assertGreater(report["pytest_collection_count"], 0)
        self.assertTrue(any(x.endswith("test_run_full_research_stack_smoke.py") for x in report["heavy_naming_matches"]))
        self.assertIn("smoke", report["tests_by_marker"])

    def test_audit_cli_writes_json_and_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_json = root / "validation_runtime_audit.json"
            out_md = root / "validation_runtime_audit.md"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/audit_validation_runtime.py",
                    "--tests-root",
                    "cajas/tests",
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                ],
                check=True,
            )
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("tests_by_marker", payload)


if __name__ == "__main__":
    unittest.main()
