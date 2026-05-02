from __future__ import annotations
import subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow, pytest.mark.full]

class RunFullResearchStackSmokeTests(unittest.TestCase):
    def test_smoke_outputs(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/'full'
            subprocess.run([sys.executable,'cajas/scripts/run_full_research_stack_smoke.py','--out-root',str(out)],check=True)
            self.assertTrue((out/'stable_repro'/'stable_reproducibility_report.json').exists())
            self.assertTrue((out/'final'/'final_readiness_packet.json').exists())
            self.assertTrue((out/'governance'/'research_governance_audit.json').exists())
            self.assertTrue((out/'bundle'/'final_research_bundle.json').exists())
if __name__=='__main__': unittest.main()
