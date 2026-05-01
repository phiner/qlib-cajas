from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_pipeline_manifest import build_research_pipeline_manifest


class ResearchPipelineManifestTests(unittest.TestCase):
    def test_manifest_inventory_and_checksums(self) -> None:
        with TemporaryDirectory() as tmp:
            d = Path(tmp)
            f = d / "a.json"
            f.write_text("{}", encoding="utf-8")
            rep = build_research_pipeline_manifest(root=d)
            self.assertTrue(rep["artifact_inventory"])
            self.assertIn("sha256", rep["artifact_inventory"][0])


if __name__ == "__main__":
    unittest.main()
