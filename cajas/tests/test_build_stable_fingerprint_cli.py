from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class BuildStableFingerprintCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp); Path(d,'a.json').write_text('{}',encoding='utf-8'); out=d/'fp.json'
            subprocess.run([sys.executable,'cajas/scripts/build_stable_fingerprint.py','--root',str(d),'--out',str(out)],check=True)
            self.assertTrue(out.exists())
if __name__=='__main__': unittest.main()
