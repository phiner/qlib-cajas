from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.recorders.dry_run_recorder import DryRunRecorder


class DryRunRecorderTests(unittest.TestCase):
    def test_write_all_creates_expected_files(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            recorder = DryRunRecorder(tmp_dir, run_name="r1")
            paths = recorder.write_all(
                manifest={"k": "v"},
                config_snapshot={"a": 1},
                workflow_summary={"b": 2},
                validation_report={"c": 3},
            )
            self.assertTrue(paths.manifest_path.exists())
            self.assertTrue(paths.config_snapshot_path.exists())
            self.assertTrue(paths.workflow_summary_path.exists())
            self.assertTrue(paths.validation_report_path.exists())
            for p in (
                paths.manifest_path,
                paths.config_snapshot_path,
                paths.workflow_summary_path,
                paths.validation_report_path,
            ):
                json.loads(p.read_text(encoding="utf-8"))

    def test_existing_run_dir_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            Path(tmp_dir, "dupe").mkdir()
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                DryRunRecorder(tmp_dir, run_name="dupe")


if __name__ == "__main__":
    unittest.main()
