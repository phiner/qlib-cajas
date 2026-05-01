from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.dashboard_export import export_dashboard_data


class DashboardExportTests(unittest.TestCase):
    def test_writes_files_and_warns_without_runs(self) -> None:
        with TemporaryDirectory() as tmp:
            reg = Path(tmp) / "runs.jsonl"
            reg.write_text("", encoding="utf-8")
            rep = export_dashboard_data(registry_path=reg, output_dir=tmp, run_name="dash", baseline_run_dirs=None)
            self.assertGreaterEqual(len(rep.files_written), 3)
            self.assertTrue(rep.warnings)


if __name__ == "__main__":
    unittest.main()
