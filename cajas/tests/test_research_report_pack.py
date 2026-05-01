from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_report_pack import build_research_report_pack


class ResearchReportPackTests(unittest.TestCase):
    def test_writes_pack(self) -> None:
        base = Path("tmp/cajas/baseline_runs/phase20_local_baseline")
        reg = Path("tmp/cajas/run_registry/runs.jsonl")
        if not base.exists() or not reg.exists():
            self.skipTest("required local artifacts not found")
        with TemporaryDirectory() as tmp:
            rep = build_research_report_pack(
                output_dir=tmp,
                run_name="r",
                title="T",
                registry_path=reg,
                baseline_run_dir=base,
            )
            self.assertFalse(rep.trading_sections_present)
            self.assertEqual(len(rep.files_written), 3)


if __name__ == "__main__":
    unittest.main()
