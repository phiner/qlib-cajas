from __future__ import annotations
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from cajas.reports.artifact_lineage import build_artifact_lineage
class ArtifactLineageTests(unittest.TestCase):
    def test_nodes_present(self):
        with TemporaryDirectory() as tmp:
            Path(tmp,'a.json').write_text('{}',encoding='utf-8')
            self.assertTrue(build_artifact_lineage(root=tmp)['nodes'])
if __name__=='__main__': unittest.main()
