from __future__ import annotations
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_artifact_lineage import main


class BuildArtifactLineageCliTests(unittest.TestCase):
    def test_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            Path(d, "a.json").write_text("{}", encoding="utf-8")
            j = d / "lineage.json"
            m = d / "lineage.md"
            code = main(["--root", str(d), "--out-json", str(j), "--out-md", str(m)])
            self.assertEqual(code, 0)
            self.assertTrue(j.exists())
            self.assertTrue(m.exists())


if __name__ == "__main__":
    unittest.main()
