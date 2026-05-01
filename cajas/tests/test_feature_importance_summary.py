from __future__ import annotations

import unittest
from pathlib import Path

from cajas.baseline.feature_importance_summary import summarize_feature_importance_across_runs


class FeatureImportanceSummaryTests(unittest.TestCase):
    def test_summary_report(self) -> None:
        run = Path("tmp/cajas/baseline_runs/phase20_local_baseline")
        if not run.exists():
            self.skipTest("baseline run not found")
        rep = summarize_feature_importance_across_runs(run_dirs=[run], top_k=10)
        self.assertGreaterEqual(rep.run_count, 1)
        self.assertFalse(rep.trading_logic_present)


if __name__ == "__main__":
    unittest.main()
