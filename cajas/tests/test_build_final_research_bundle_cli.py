from __future__ import annotations
import json,subprocess,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
class BuildFinalResearchBundleCliTests(unittest.TestCase):
    def test_cli(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp)
            fr=d/'fr.json'; sr=d/'sr.json'; gv=d/'gv.json'; ln=d/'ln.json'; rc=d/'rc.json'; rv=d/'rv.json'; ci=d/'ci.json'; sm=d/'sum.md'
            fr.write_text(json.dumps({'final_status':'blocked','blocked_actions':[]}),encoding='utf-8')
            sr.write_text(json.dumps({'final_status':'stable_reproducible'}),encoding='utf-8')
            gv.write_text(json.dumps({'status':'pass'}),encoding='utf-8')
            ln.write_text(json.dumps({'nodes':[]}),encoding='utf-8')
            rc.write_text(json.dumps({'summary':{}}),encoding='utf-8')
            rv.write_text(json.dumps({'overall_review_state':'blocked','permitted_next_actions':[],'review_checklist':[]}),encoding='utf-8')
            ci.write_text(json.dumps({'tiers':[]}),encoding='utf-8')
            sm.write_text('x',encoding='utf-8')
            oj=d/'bundle.json'; om=d/'bundle.md'
            subprocess.run([sys.executable,'cajas/scripts/build_final_research_bundle.py','--root',str(d),'--final-readiness-packet',str(fr),'--final-readiness-summary',str(sm),'--stable-reproducibility-report',str(sr),'--governance-audit',str(gv),'--artifact-lineage',str(ln),'--run-catalog',str(rc),'--offline-review-packet',str(rv),'--ci-validation-plan',str(ci),'--out-json',str(oj),'--out-md',str(om)],check=True)
            self.assertTrue(oj.exists()); self.assertTrue(om.exists())
if __name__=='__main__': unittest.main()
