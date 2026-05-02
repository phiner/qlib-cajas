from __future__ import annotations

import unittest

from cajas.reports.normalization_coverage_report import build_normalization_coverage_report


class NormalizationCoverageReportTests(unittest.TestCase):
    def test_reports_supported_and_preserved_fields(self) -> None:
        report = build_normalization_coverage_report(
            stable_fingerprint={
                "included_files": [
                    {"relative_path": "a.json", "stable_hash": "x"},
                    {"relative_path": "b.md", "stable_hash": "y"},
                    {"relative_path": "c.csv", "stable_hash": "z"},
                ]
            }
        )
        self.assertIn(".json", report["supported_file_types"])
        self.assertIn(".csv", report["skipped_file_types"])
        self.assertIn("metrics", report["preserved_field_paths"])


if __name__ == "__main__":
    unittest.main()

