from __future__ import annotations

import unittest

from cajas.reports.qlib_model_training_contract import QlibModelTrainingContract


class QlibModelTrainingContractTests(unittest.TestCase):
    def test_to_dict(self) -> None:
        c = QlibModelTrainingContract(
            schema_version="v1",
            run_id="r1",
            created_at_utc="2026-01-01T00:00:00+00:00",
            handler_input_path="a",
            handler_manifest_path="b",
            dataset_contract_path="c",
            handler_smoke_report_path="d",
            instrument_col="instrument",
            datetime_col="datetime",
            label_col="future_direction_8",
            feature_columns=["close"],
            split_ratios={"train": 0.7, "valid": 0.15, "test": 0.15},
            row_count=10,
        )
        self.assertEqual(c.to_dict()["run_id"], "r1")


if __name__ == "__main__":
    unittest.main()
