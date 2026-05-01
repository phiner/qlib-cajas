from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class BuildResearchPipelineManifestCliTests(unittest.TestCase):
    def test_cli_writes_output(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "a.json").write_text("{}", encoding="utf-8")
            out = d / "manifest.json"
            subprocess.run([sys.executable, "cajas/scripts/build_research_pipeline_manifest.py", "--root", str(d), "--out", str(out)], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
