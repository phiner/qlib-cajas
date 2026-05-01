from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.baseline_report_pack import build_baseline_report_pack


class BaselineReportPackTests(unittest.TestCase):
    def test_build_from_real_fixture_run(self) -> None:
        run_dir = Path("tmp/cajas/baseline_runs/phase20_local_baseline")
        if not run_dir.exists():
            self.skipTest("phase20_local_baseline fixture run not found")
        with TemporaryDirectory() as tmp:
            rep = build_baseline_report_pack(
                run_dir=run_dir,
                output_dir=tmp,
                run_name="pack",
                write_artifacts=True,
                top_k_features=10,
            )
            self.assertFalse(rep.trading_metrics_present)
            self.assertIn("valid", rep.prediction_review)


if __name__ == "__main__":
    unittest.main()
