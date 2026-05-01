from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class BuildArtifactLineageCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp); Path(d,'a.json').write_text('{}',encoding='utf-8'); j=d/'lineage.json'; m=d/'lineage.md'
            subprocess.run([sys.executable,'cajas/scripts/build_artifact_lineage.py','--root',str(d),'--out-json',str(j),'--out-md',str(m)],check=True)
            self.assertTrue(j.exists()); self.assertTrue(m.exists())
if __name__=='__main__': unittest.main()
