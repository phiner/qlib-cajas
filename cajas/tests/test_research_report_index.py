from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.research_report_index import build_research_report_index


class ResearchReportIndexTests(unittest.TestCase):
    def test_groups_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "label_variant_comparison_report.json").write_text("{}", encoding="utf-8")
            (root / "qlib_readiness_report.json").write_text("{}", encoding="utf-8")
            idx = build_research_report_index(root_dir=root)
            self.assertIn("label_variant_comparison_report.json", idx["groups"]["labels"])
            self.assertIn("qlib_readiness_report.json", idx["groups"]["readiness"])


if __name__ == "__main__":
    unittest.main()

