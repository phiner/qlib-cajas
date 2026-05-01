from __future__ import annotations

import unittest

from cajas.baseline.classification_metrics import (
    compute_classification_metrics,
    confusion_matrix_to_rows,
)


class ClassificationMetricsTests(unittest.TestCase):
    def test_metrics_computed(self) -> None:
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 2, 0, 2, 1]
        metrics = compute_classification_metrics(
            y_true=y_true,
            y_pred=y_pred,
            labels=[0, 1, 2],
            label_names=["down", "flat", "up"],
        )
        self.assertIn("accuracy", metrics)
        self.assertIn("macro_f1", metrics)
        self.assertIn("weighted_f1", metrics)
        self.assertIn("per_class", metrics)

    def test_confusion_matrix_rows_stable(self) -> None:
        rows = confusion_matrix_to_rows(
            matrix=[[2, 0, 1], [0, 3, 0], [1, 0, 4]],
            label_names=["down", "flat", "up"],
        )
        self.assertEqual(rows[0]["true_label"], "down")
        self.assertEqual(rows[0]["pred_down"], 2)
        self.assertEqual(rows[2]["pred_up"], 4)

    def test_no_trading_metrics_present(self) -> None:
        y_true = [0, 1, 2]
        y_pred = [0, 1, 1]
        metrics = compute_classification_metrics(
            y_true=y_true,
            y_pred=y_pred,
            labels=[0, 1, 2],
            label_names=["down", "flat", "up"],
        )
        forbidden = {"profit", "return", "sharpe", "drawdown", "pnl", "win_rate"}
        self.assertTrue(forbidden.isdisjoint(metrics.keys()))


if __name__ == "__main__":
    unittest.main()
