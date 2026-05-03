from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.build_dataset_quality_report import main as build_dataset_quality_report_main
from cajas.scripts.build_feature_schema_manifest import main as build_feature_schema_manifest_main
from cajas.scripts.build_label_coverage_diagnostics import main as build_label_coverage_diagnostics_main
from cajas.scripts.build_offline_research_queue_summary import main as build_offline_research_queue_summary_main
from cajas.scripts.build_time_coverage_diagnostics import main as build_time_coverage_diagnostics_main
from cajas.scripts.run_chunked_feature_dry_run import main as run_chunked_feature_dry_run_main


class DatasetQualityModularCliTests(unittest.TestCase):
    def test_modular_clis_write_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,up\n"
                "EURUSD,2025-01-01 00:15:00,1.1,down\n",
                encoding="utf-8",
            )

            self.assertEqual(
                build_dataset_quality_report_main(
                    [
                        "--input",
                        str(csv),
                        "--labels",
                        "future_direction_8",
                        "--feature-col",
                        "feature_a",
                        "--out-json",
                        str(root / "dataset_quality_report.json"),
                        "--out-md",
                        str(root / "dataset_quality_report.md"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                build_label_coverage_diagnostics_main(
                    [
                        "--input",
                        str(csv),
                        "--labels",
                        "future_direction_8",
                        "--out-json",
                        str(root / "label_coverage_diagnostics.json"),
                        "--out-md",
                        str(root / "label_coverage_diagnostics.md"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                build_time_coverage_diagnostics_main(
                    [
                        "--input",
                        str(csv),
                        "--out-json",
                        str(root / "time_coverage_diagnostics.json"),
                        "--out-md",
                        str(root / "time_coverage_diagnostics.md"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                run_chunked_feature_dry_run_main(
                    [
                        "--input",
                        str(csv),
                        "--labels",
                        "future_direction_8",
                        "--feature-col",
                        "feature_a",
                        "--out-json",
                        str(root / "chunked_feature_dry_run.json"),
                        "--out-md",
                        str(root / "chunked_feature_dry_run.md"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                build_feature_schema_manifest_main(
                    [
                        "--input",
                        str(csv),
                        "--feature-col",
                        "feature_a",
                        "--out-json",
                        str(root / "feature_schema_manifest.json"),
                        "--out-md",
                        str(root / "feature_schema_manifest.md"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                build_offline_research_queue_summary_main(
                    [
                        "--input",
                        str(csv),
                        "--labels",
                        "future_direction_8",
                        "--out-json",
                        str(root / "offline_research_queue_summary.json"),
                        "--out-md",
                        str(root / "offline_research_queue_summary.md"),
                    ]
                ),
                0,
            )

            payload = json.loads((root / "dataset_quality_report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["scope"], "offline_research_only")
            self.assertTrue((root / "feature_schema_manifest.md").exists())

    def test_missing_input_fails_cleanly(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            try:
                ret = build_dataset_quality_report_main(
                    [
                        "--input",
                        str(root / "missing.csv"),
                        "--labels",
                        "future_direction_8",
                        "--out-json",
                        str(root / "x.json"),
                        "--out-md",
                        str(root / "x.md"),
                    ]
                )
                self.fail("Expected FileNotFoundError")
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    unittest.main()



if __name__ == "__main__":
    unittest.main()
