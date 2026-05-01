from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_decision_report import build_research_decision_report


class ResearchDecisionReportTests(unittest.TestCase):
    def test_report_contains_required_sections_and_no_trading_recommendations(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "ext"
            run.mkdir()
            (run / "metrics_holdout.json").write_text(json.dumps({"accuracy": 0.5, "macro_f1": 0.33}), encoding="utf-8")
            (run / "external_holdout_dataset_summary.json").write_text(json.dumps({"label_col": "future_direction_8"}), encoding="utf-8")
            report = build_research_decision_report(external_run_dir=run, output_dir=root, run_name="r", write_artifacts=True)
            self.assertFalse(report.trading_profit_backtest_recommendations_present)
            payload = json.loads((Path(report.output_dir) / "research_decision_report.json").read_text(encoding="utf-8"))
            self.assertIn("decision_summary", payload)
            self.assertIn("recommended_next_phase", payload)
            forbidden_text = json.dumps(payload).lower()
            self.assertNotIn("buy signal", forbidden_text)
            self.assertNotIn("pnl optimization", forbidden_text)


if __name__ == "__main__":
    unittest.main()
