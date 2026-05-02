from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from cajas.audits.leakage_drift_audit import run_leakage_drift_audit


class LeakageDriftAuditTests(unittest.TestCase):
    def test_detects_forbidden_feature(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            fc = Path(tmp) / "fc.json"
            pd.DataFrame([{"datetime": "a", "f1": 1.0, "future_return_8": 0.1, "future_direction_8": "up"}]).to_csv(tr, index=False)
            pd.DataFrame([{"datetime": "b", "f1": 1.2, "future_return_8": 0.2, "future_direction_8": "down"}]).to_csv(ho, index=False)
            fc.write_text(json.dumps({"feature_columns": ["f1", "future_return_8"]}), encoding="utf-8")
            rep = run_leakage_drift_audit(
                train_path=tr,
                holdout_path=ho,
                feature_columns_path=fc,
                label_col="future_direction_8",
                output_dir=Path(tmp),
                run_name="r",
            )
            self.assertIn("future_return_8", rep["forbidden_feature_columns"])

    def test_sample_only_mode_is_supported(self) -> None:
        with TemporaryDirectory() as tmp:
            tr = Path(tmp) / "tr.csv"
            ho = Path(tmp) / "ho.csv"
            fc = Path(tmp) / "fc.json"
            rows = [
                {"datetime": f"2025-01-01T00:{i:02d}:00Z", "f1": float(i), "future_direction_8": "up" if i % 2 == 0 else "down"}
                for i in range(20)
            ]
            pd.DataFrame(rows).to_csv(tr, index=False)
            pd.DataFrame(rows).to_csv(ho, index=False)
            fc.write_text(json.dumps({"feature_columns": ["f1"]}), encoding="utf-8")
            rep = run_leakage_drift_audit(
                train_path=tr,
                holdout_path=ho,
                feature_columns_path=fc,
                label_col="future_direction_8",
                output_dir=Path(tmp),
                run_name="r2",
                sample_only=True,
            )
            self.assertIn("loading_decisions", rep)


if __name__ == "__main__":
    unittest.main()
