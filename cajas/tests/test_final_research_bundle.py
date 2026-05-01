from __future__ import annotations
import unittest
from cajas.reports.final_research_bundle import build_final_research_bundle
class FinalResearchBundleTests(unittest.TestCase):
    def test_bundle_status(self):
        rep=build_final_research_bundle(root='/tmp/x',final_readiness_packet={'final_status':'blocked','blocked_actions':[]},final_readiness_summary_path='/tmp/x.md',stable_repro_report={'final_status':'stable_reproducible'},governance_audit={'status':'pass'},artifact_lineage={'nodes':[]},run_catalog={'summary':{}},offline_review_packet={'overall_review_state':'blocked','permitted_next_actions':[],'review_checklist':[]},ci_validation_plan={'tiers':[]})
        self.assertEqual(rep['bundle_status'],'blocked')
if __name__=='__main__': unittest.main()
