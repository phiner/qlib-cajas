from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


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

            commands = [
                [
                    "cajas/scripts/build_dataset_quality_report.py",
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
                ],
                [
                    "cajas/scripts/build_label_coverage_diagnostics.py",
                    "--input",
                    str(csv),
                    "--labels",
                    "future_direction_8",
                    "--out-json",
                    str(root / "label_coverage_diagnostics.json"),
                    "--out-md",
                    str(root / "label_coverage_diagnostics.md"),
                ],
                [
                    "cajas/scripts/build_time_coverage_diagnostics.py",
                    "--input",
                    str(csv),
                    "--out-json",
                    str(root / "time_coverage_diagnostics.json"),
                    "--out-md",
                    str(root / "time_coverage_diagnostics.md"),
                ],
                [
                    "cajas/scripts/run_chunked_feature_dry_run.py",
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
                ],
                [
                    "cajas/scripts/build_feature_schema_manifest.py",
                    "--input",
                    str(csv),
                    "--feature-col",
                    "feature_a",
                    "--out-json",
                    str(root / "feature_schema_manifest.json"),
                    "--out-md",
                    str(root / "feature_schema_manifest.md"),
                ],
                [
                    "cajas/scripts/build_offline_research_queue_summary.py",
                    "--input",
                    str(csv),
                    "--labels",
                    "future_direction_8",
                    "--out-json",
                    str(root / "offline_research_queue_summary.json"),
                    "--out-md",
                    str(root / "offline_research_queue_summary.md"),
                ],
            ]
            for cmd in commands:
                subprocess.run([sys.executable, *cmd], check=True)

            payload = json.loads((root / "dataset_quality_report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["scope"], "offline_research_only")
            self.assertTrue((root / "feature_schema_manifest.md").exists())

    def test_missing_input_fails_cleanly(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            proc = subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/build_dataset_quality_report.py",
                    "--input",
                    str(root / "missing.csv"),
                    "--labels",
                    "future_direction_8",
                    "--out-json",
                    str(root / "x.json"),
                    "--out-md",
                    str(root / "x.md"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
