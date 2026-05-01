from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class AuditResearchGovernanceCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/'audit.json'
            subprocess.run([sys.executable,'cajas/scripts/audit_research_governance.py','--root','cajas','--out',str(out)],check=True)
            self.assertTrue(out.exists())
if __name__=='__main__': unittest.main()
