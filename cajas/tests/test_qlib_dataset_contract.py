from __future__ import annotations

import unittest

from cajas.reports.qlib_dataset_contract import QlibDatasetContract


class QlibDatasetContractTests(unittest.TestCase):
    def test_schema_object_to_dict(self) -> None:
        obj = QlibDatasetContract(
            schema_version="v1",
            dataset_id="d1",
            created_at_utc="2026-01-01T00:00:00+00:00",
            source_contract_path="",
            source_integration_packet_path="",
            instrument_col="instrument",
            datetime_col="datetime",
            feature_columns=["close"],
            label_columns=["future_direction_8"],
            required_columns=["instrument", "datetime", "future_direction_8"],
            optional_columns=[],
            split_metadata={"available": False},
            time_range={"min": "2025-01-01", "max": "2025-01-02"},
            instrument_count=1,
            row_count=2,
            null_summary={},
            dtype_summary={},
            numeric_feature_count=1,
            non_numeric_feature_columns=[],
            label_distribution_summary={},
        )
        self.assertEqual(obj.to_dict()["dataset_id"], "d1")


if __name__ == "__main__":
    unittest.main()
