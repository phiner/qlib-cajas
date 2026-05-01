from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.baseline.baseline_artifact_inspector import inspect_baseline_run_artifacts


class BaselineArtifactInspectorTests(unittest.TestCase):
    def _write_complete_run(self, base: Path) -> None:
        (base / "run_manifest.json").write_text(json.dumps({"training_executed": True, "qlib_workflow_executed": False}), encoding="utf-8")
        (base / "training_config.json").write_text(json.dumps({"run_name": "r1"}), encoding="utf-8")
        (base / "feature_columns.json").write_text(json.dumps({"feature_columns": ["f1", "f2"]}), encoding="utf-8")
        (base / "label_encoding.json").write_text(json.dumps({"mapping": {"down": 0, "flat": 1, "up": 2}}), encoding="utf-8")
        (base / "label_distribution.json").write_text(json.dumps({"train": {"down": 1}}), encoding="utf-8")
        (base / "metrics_valid.json").write_text(json.dumps({"accuracy": 0.5}), encoding="utf-8")
        (base / "metrics_test.json").write_text(json.dumps({"accuracy": 0.4}), encoding="utf-8")
        (base / "model_metadata.json").write_text(json.dumps({"model_family_used": "LightGBM", "target_label": "future_direction_8", "feature_count": 2}), encoding="utf-8")
        for name in [
            "confusion_matrix_valid.csv",
            "confusion_matrix_test.csv",
            "predictions_valid.csv",
            "predictions_test.csv",
        ]:
            (base / name).write_text("a,b\n1,2\n", encoding="utf-8")
        (base / "model.joblib").write_bytes(b"dummy")

    def test_complete_run_directory_passes(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "run"
            run_dir.mkdir()
            self._write_complete_run(run_dir)
            report = inspect_baseline_run_artifacts(run_dir)
            self.assertTrue(report.required_files_present)
            self.assertEqual(report.model_family_used, "LightGBM")

    def test_missing_required_file_produces_issue(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "run"
            run_dir.mkdir()
            self._write_complete_run(run_dir)
            (run_dir / "model.joblib").unlink()
            report = inspect_baseline_run_artifacts(run_dir)
            self.assertFalse(report.required_files_present)
            self.assertTrue(any(i.code == "missing_required_file" for i in report.issues))

    def test_report_serializes(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "run"
            run_dir.mkdir()
            self._write_complete_run(run_dir)
            payload = inspect_baseline_run_artifacts(run_dir).to_dict()
            json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
