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

    def test_policy_guarded_read_csv_not_counted_as_full_read_likely(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            f = root / "guarded.py"
            f.write_text(
                "from cajas.data_io.csv_loading_policy import CsvLoadingPolicy, evaluate_loading_decision\n"
                "import pandas as pd\n"
                "d = evaluate_loading_decision('x.csv', CsvLoadingPolicy())\n"
                "pd.read_csv('x.csv')\n",
                encoding="utf-8",
            )
            rep = build_data_source_audit(project_root=root, include_tasks=False)
            rec = rep["records"][0]
            self.assertTrue(rec["policy_guarded"])
            self.assertFalse(rec["reads_full_csv_likely"])


if __name__ == "__main__":
    unittest.main()
