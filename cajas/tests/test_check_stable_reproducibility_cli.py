from __future__ import annotations
import json,subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class CheckStableReproducibilityCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp); l=d/'l.json'; r=d/'r.json'; out=d/'rep.json'
            l.write_text(json.dumps({'included_files':[],'root':'a'}),encoding='utf-8')
            r.write_text(json.dumps({'included_files':[],'root':'b'}),encoding='utf-8')
            subprocess.run([sys.executable,'cajas/scripts/check_stable_reproducibility.py','--left',str(l),'--right',str(r),'--out',str(out)],check=True)
            self.assertTrue(out.exists())
if __name__=='__main__': unittest.main()
