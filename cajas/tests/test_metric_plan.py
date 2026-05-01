from __future__ import annotations

import json
import unittest

from cajas.baseline.metric_plan import build_multiclass_metric_plan


class MetricPlanTests(unittest.TestCase):
    def test_primary_metric_is_classification_metric(self) -> None:
        plan = build_multiclass_metric_plan()
        self.assertEqual(plan.primary_metric, "macro_f1")

    def test_forbidden_trading_metrics_absent(self) -> None:
        plan = build_multiclass_metric_plan()
        names = {m.name for m in plan.metrics}
        for forbidden in {"profit", "return", "sharpe", "drawdown"}:
            self.assertNotIn(forbidden, names)

    def test_serialization(self) -> None:
        plan = build_multiclass_metric_plan()
        payload = plan.to_dict()
        self.assertEqual(payload["task_type"], "multiclass_classification")
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
