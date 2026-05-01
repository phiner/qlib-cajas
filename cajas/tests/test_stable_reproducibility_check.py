from __future__ import annotations
import unittest
from cajas.reports.stable_reproducibility_check import build_stable_reproducibility_report
class StableReproducibilityCheckTests(unittest.TestCase):
    def test_report(self) -> None:
        l={"root":"a","included_files":[{"relative_path":"x","stable_hash":"1"}],"skipped_files":[]}
        r={"root":"b","included_files":[{"relative_path":"x","stable_hash":"1"}],"skipped_files":[]}
        self.assertEqual(build_stable_reproducibility_report(left=l,right=r)["final_status"],"stable_reproducible")
if __name__ == "__main__": unittest.main()
