from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.dataset_quality_research import build_dataset_quality_research_artifacts
from cajas.scripts.build_dataset_quality_research_bundle import main as build_dataset_quality_research_bundle_main


class DatasetQualityResearchBundleTests(unittest.TestCase):
    def test_build_bundle_reports_coverage_and_imbalance(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,feature_b,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,2.0,up\n"
                "EURUSD,2025-01-01 00:15:00,1.1,2.1,up\n"
                "EURUSD,2025-01-01 00:30:00,1.2,2.2,up\n"
                "EURUSD,2025-01-01 00:45:00,1.3,2.3,down\n",
                encoding="utf-8",
            )
            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv,
                label_columns=["future_direction_8"],
                feature_columns=["feature_a", "feature_b"],
                chunk_size=2,
                imbalance_warn_threshold=0.7,
            )
            rep = bundle["dataset_quality_report"]
            self.assertEqual(rep["row_count"], 4)
            self.assertEqual(rep["time_coverage"]["datetime_parse_failed_count"], 0)
            self.assertEqual(rep["instrument_summary"]["unique_instrument_count"], 1)
            label_row = rep["label_diagnostics"][0]
            self.assertTrue(label_row["imbalance_warning"])
            self.assertEqual(bundle["feature_schema_manifest"]["features"][0]["name"], "feature_a")

            # New fields
            self.assertIn("schema_version", rep)
            self.assertIn("status", rep)
            self.assertIn("quality_score", rep)
            self.assertIn("label_review_buckets", rep)
            self.assertIn("feature_readiness", rep)
            self.assertIn("ranked_review_items", bundle["offline_research_queue_summary"])

            # Quality score structure
            qs = rep["quality_score"]
            self.assertIn("score", qs)
            self.assertIn("max_score", qs)
            self.assertIn("grade", qs)
            self.assertIn("components", qs)
            self.assertGreater(len(qs["components"]), 0)

            # Label review buckets
            self.assertGreater(len(rep["label_review_buckets"]), 0)
            bucket = rep["label_review_buckets"][0]
            self.assertIn("priority", bucket)
            self.assertIn("bucket", bucket)
            self.assertIn("recommended_action", bucket)

    def test_cli_writes_bundle_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            out = root / "out"
            csv.write_text(
                "instrument,datetime,feature_a,feature_b,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,2.0,up\n"
                "EURUSD,2025-01-01 00:15:00,1.1,2.1,down\n",
                encoding="utf-8",
            )
            code = build_dataset_quality_research_bundle_main(
                [
                    "--input-csv",
                    str(csv),
                    "--out-dir",
                    str(out),
                    "--label-col",
                    "future_direction_8",
                    "--feature-col",
                    "feature_a",
                    "--feature-col",
                    "feature_b",
                    "--chunk-size",
                    "1",
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((out / "dataset_quality_report.json").exists())
            self.assertTrue((out / "feature_schema_manifest.json").exists())
            self.assertTrue((out / "offline_research_queue_summary.json").exists())
            payload = json.loads((out / "dataset_quality_report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["scope"], "offline_research_only")


if __name__ == "__main__":
    unittest.main()
