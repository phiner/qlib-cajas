from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_roadmap_report import build_research_roadmap_report


class ResearchRoadmapReportTests(unittest.TestCase):
    def test_trading_blocked_flag(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = build_research_roadmap_report(output_dir=Path(tmp), run_name="r")
            self.assertTrue(rep["trading_backtest_discussion_blocked"])


if __name__ == "__main__":
    unittest.main()
