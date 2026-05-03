from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow]


class RunDatasetQualitySmokeTests(unittest.TestCase):
    def test_smoke_writes_expected_tree(self) -> None:
        with TemporaryDirectory() as tmp:
            out_root = Path(tmp) / "smoke"
            run = subprocess.run(
                [
                    sys.executable,
                    "cajas/scripts/run_dataset_quality_smoke.py",
                    "--out-root",
                    str(out_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            summary = json.loads(run.stdout.strip())
            self.assertEqual(summary["status"], "ok")

            expected = [
                "dataset_quality/dataset_quality_report.json",
                "dataset_quality/dataset_quality_report.md",
                "labels/label_coverage_diagnostics.json",
                "labels/label_coverage_diagnostics.md",
                "time/time_coverage_diagnostics.json",
                "time/time_coverage_diagnostics.md",
                "features/chunked_feature_dry_run.json",
                "features/chunked_feature_dry_run.md",
                "features/feature_schema_manifest.json",
                "features/feature_schema_manifest.md",
                "research_queue/offline_research_queue_summary.json",
                "research_queue/offline_research_queue_summary.md",
            ]
            for rel in expected:
                self.assertTrue((out_root / rel).exists(), rel)

            queue = json.loads((out_root / "research_queue/offline_research_queue_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(queue["scope"], "offline_research_only")


if __name__ == "__main__":
    unittest.main()
