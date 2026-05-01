from __future__ import annotations
import json,subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class BuildOfflineReviewPacketCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp)
            fr=d/'fr.json'; sr=d/'sr.json'; gv=d/'gv.json'; ln=d/'ln.json'; rc=d/'rc.json'
            fr.write_text(json.dumps({'final_status':'blocked','blocked_actions':[],'permitted_next_actions':[]}),encoding='utf-8')
            sr.write_text(json.dumps({'final_status':'stable_reproducible'}),encoding='utf-8')
            gv.write_text(json.dumps({'status':'pass'}),encoding='utf-8')
            ln.write_text(json.dumps({'nodes':[]}),encoding='utf-8')
            rc.write_text(json.dumps({'summary':{}}),encoding='utf-8')
            oj=d/'review.json'; om=d/'review.md'
            subprocess.run([sys.executable,'cajas/scripts/build_offline_review_packet.py','--final-readiness-packet',str(fr),'--stable-reproducibility-report',str(sr),'--governance-audit',str(gv),'--artifact-lineage',str(ln),'--run-catalog',str(rc),'--out-json',str(oj),'--out-md',str(om)],check=True)
            self.assertTrue(oj.exists()); self.assertTrue(om.exists())
if __name__=='__main__': unittest.main()
