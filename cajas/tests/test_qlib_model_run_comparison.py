from __future__ import annotations

import unittest

from cajas.reports.qlib_model_run_comparison import build_qlib_model_run_comparison


class QlibModelRunComparisonTests(unittest.TestCase):
    def test_ranking(self) -> None:
        rep = build_qlib_model_run_comparison(records=[{"run_id": "a", "metrics": {"macro_f1": 0.2}}, {"run_id": "b", "metrics": {"macro_f1": 0.1}}])
        self.assertEqual(rep["ranked_runs"][0]["run_id"], "a")


if __name__ == "__main__":
    unittest.main()
