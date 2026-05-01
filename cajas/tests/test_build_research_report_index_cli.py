from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildResearchReportIndexCliTests(unittest.TestCase):
    def test_cli_outputs_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            (artifacts / "seed_stability_report.json").write_text("{}", encoding="utf-8")
            out = root / "index"
            subprocess.run(
                [sys.executable, "cajas/scripts/build_research_report_index.py", "--root-dir", str(artifacts), "--out-dir", str(out)],
                check=True,
            )
            self.assertTrue((out / "research_report_index.json").exists())
            self.assertTrue((out / "research_report_index.md").exists())


if __name__ == "__main__":
    unittest.main()

