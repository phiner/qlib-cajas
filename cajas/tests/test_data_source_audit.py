from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.data_source_audit import build_data_source_audit


class DataSourceAuditTests(unittest.TestCase):
    def test_static_audit_detects_read_csv_usage(self) -> None:
        rep = build_data_source_audit(project_root="cajas", data_root="/home/phiner/projects/research/data")
        self.assertIn("read_csv_paths", rep)
        self.assertGreater(len(rep["read_csv_paths"]), 0)

    def test_cli_writes_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "data_source_audit.json"
            out_md = Path(tmp) / "data_source_audit.md"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/audit_data_sources.py",
                    "--project-root",
                    "cajas",
                    "--data-root",
                    "/home/phiner/projects/research/data",
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
            self.assertIn("summary", payload)


if __name__ == "__main__":
    unittest.main()
