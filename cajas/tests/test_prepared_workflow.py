from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.workflows.prepared_workflow import PreparedWorkflow, PreparedWorkflowConfig


class PreparedWorkflowTests(unittest.TestCase):
    def _write_csv(self, tmp_dir: str, rows: list[dict]) -> Path:
        path = Path(tmp_dir) / "prepared_dataset.csv"
        pd.DataFrame(rows).to_csv(path, index=False)
        return path

    def _rows(self) -> list[dict]:
        return [
            {
                "datetime": "2025-01-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.1,
                "high": 1.2,
                "low": 1.0,
                "close": 1.15,
                "volume": 100,
                "return_1": 0.001,
                "future_close_8": 1.16,
                "future_return_8": 0.01,
                "future_direction_8": "up",
            },
            {
                "datetime": "2025-10-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.15,
                "high": 1.22,
                "low": 1.12,
                "close": 1.2,
                "volume": 120,
                "return_1": -0.001,
                "future_close_8": 1.18,
                "future_return_8": -0.01,
                "future_direction_8": "down",
            },
            {
                "datetime": "2025-12-01T00:00:00Z",
                "symbol": "EURUSD",
                "timeframe": "15m",
                "open": 1.2,
                "high": 1.25,
                "low": 1.18,
                "close": 1.24,
                "volume": 125,
                "return_1": 0.002,
                "future_close_8": 1.26,
                "future_return_8": 0.005,
                "future_direction_8": "flat",
            },
        ]

    def test_dry_run_returns_segment_summary(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            summary = PreparedWorkflow(PreparedWorkflowConfig(csv_path=str(path))).dry_run()
            self.assertEqual(summary.label_col, "future_direction_8")
            self.assertEqual(len(summary.segment_shapes), 3)

    def test_feature_label_row_counts_match(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            wf = PreparedWorkflow(PreparedWorkflowConfig(csv_path=str(path)))
            x, y = wf.prepare("train")
            self.assertEqual(len(x), len(y))

    def test_leakage_columns_excluded(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            summary = PreparedWorkflow(PreparedWorkflowConfig(csv_path=str(path))).dry_run()
            self.assertFalse(summary.leakage_columns_in_features)
            self.assertNotIn("future_close_8", summary.feature_columns)
            self.assertNotIn("future_return_8", summary.feature_columns)

    def test_unknown_segment_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            wf = PreparedWorkflow(PreparedWorkflowConfig(csv_path=str(path)))
            with self.assertRaisesRegex(ValueError, "Unknown segment"):
                wf.prepare("unknown")

    def test_empty_segment_raises(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            wf = PreparedWorkflow(
                PreparedWorkflowConfig(
                    csv_path=str(path),
                    segments={"train": ("2024-01-01", "2024-01-02")},
                )
            )
            with self.assertRaisesRegex(ValueError, "Segment has zero rows"):
                wf.prepare("train")

    def test_summary_to_dict_json_ready(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            path = self._write_csv(tmp_dir, self._rows())
            summary = PreparedWorkflow(PreparedWorkflowConfig(csv_path=str(path))).dry_run()
            data = summary.to_dict()
            self.assertIn("segment_shapes", data)
            self.assertIsInstance(data["segment_shapes"], list)


if __name__ == "__main__":
    unittest.main()
