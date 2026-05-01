from __future__ import annotations

import unittest

from cajas.reports.qlib_model_metrics import compute_classification_metrics


class QlibModelMetricsTests(unittest.TestCase):
    def test_metrics_keys(self) -> None:
        m = compute_classification_metrics(y_true=["up", "down"], y_pred=["up", "up"])
        self.assertIn("accuracy", m)
        self.assertIn("macro_f1", m)


if __name__ == "__main__":
    unittest.main()
