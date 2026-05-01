from __future__ import annotations
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from cajas.reports.research_run_catalog import build_research_run_catalog
class ResearchRunCatalogTests(unittest.TestCase):
    def test_catalog_summary(self):
        with TemporaryDirectory() as tmp:
            Path(tmp,'metrics.json').write_text('{}',encoding='utf-8')
            self.assertIn('metrics_files', build_research_run_catalog(root=tmp)['summary'])
if __name__=='__main__': unittest.main()
