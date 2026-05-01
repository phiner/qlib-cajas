from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.registry.registry_reports import build_run_registry_summary


class RegistryReportsTests(unittest.TestCase):
    def test_missing_registry(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = build_run_registry_summary(registry_path=Path(tmp) / "missing.jsonl")
            self.assertEqual(rep.total_records, 0)
            self.assertTrue(rep.warnings)

    def test_present_registry(self) -> None:
        reg = Path("tmp/cajas/run_registry/runs.jsonl")
        if not reg.exists():
            self.skipTest("registry not available")
        rep = build_run_registry_summary(registry_path=reg)
        self.assertGreaterEqual(rep.total_records, 1)


if __name__ == "__main__":
    unittest.main()
