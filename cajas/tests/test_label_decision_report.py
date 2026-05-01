from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.label_decision_report import build_label_decision_report


class LabelDecisionReportTests(unittest.TestCase):
    def test_no_trading_recommendations(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "comp.json"
            p.write_text(json.dumps({"rows": [{"run_name": "x", "label_mode": "multiclass", "horizon": 8, "threshold": 0.0001}]}), encoding="utf-8")
            rep = build_label_decision_report(comparison_report_path=p, output_dir=tmp, run_name="r")
            self.assertFalse(rep["trading_recommendations_present"])


if __name__ == "__main__":
    unittest.main()
