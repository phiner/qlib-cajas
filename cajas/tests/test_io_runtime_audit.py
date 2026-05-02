from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.io_runtime_audit import build_io_runtime_audit


class IoRuntimeAuditTests(unittest.TestCase):
    def test_static_audit_detects_rglob_and_smoke_nesting(self) -> None:
        rep = build_io_runtime_audit(project_root="cajas", tmp_root="tmp")
        self.assertIn("rglob_scripts", rep)
        self.assertIn("nested_smoke_scripts", rep)

    def test_cli_writes_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out_json = Path(tmp) / "io_runtime_audit.json"
            out_md = Path(tmp) / "io_runtime_audit.md"
            subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/audit_io_runtime.py",
                    "--project-root",
                    "cajas",
                    "--tmp-root",
                    "tmp",
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                ],
                check=True,
            )
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("tmp_summary", payload)


if __name__ == "__main__":
    unittest.main()
