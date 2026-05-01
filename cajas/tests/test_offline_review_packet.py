from __future__ import annotations
import unittest
from cajas.reports.offline_review_packet import build_offline_review_packet
class OfflineReviewPacketTests(unittest.TestCase):
    def test_blocked_actions_preserved(self):
        rep=build_offline_review_packet(final_readiness_packet={'final_status':'blocked','blocked_actions':['x'],'permitted_next_actions':[]},stable_reproducibility_report={'final_status':'not_stable_reproducible'},governance_audit={'status':'pass'},artifact_lineage={'nodes':[]},run_catalog={'summary':{}})
        self.assertIn('blocked_actions',rep)
if __name__=='__main__': unittest.main()
