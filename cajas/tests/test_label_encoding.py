from __future__ import annotations

import unittest

import pandas as pd

from cajas.baseline.label_encoding import (
    default_future_direction_8_encoding,
    encode_labels_for_preview,
    preview_label_encoding,
)


class LabelEncodingTests(unittest.TestCase):
    def test_default_mapping(self) -> None:
        plan = default_future_direction_8_encoding()
        self.assertEqual(plan.mapping, {"down": 0, "flat": 1, "up": 2})

    def test_preview_counts_classes(self) -> None:
        plan = default_future_direction_8_encoding()
        labels = pd.Series(["up", "down", "flat", "up"])
        preview = preview_label_encoding(labels, plan)
        self.assertEqual(preview.class_counts, {"down": 1, "flat": 1, "up": 2})
        self.assertEqual(preview.encoded_class_counts, {0: 1, 1: 1, 2: 2})

    def test_unknown_label_produces_error(self) -> None:
        plan = default_future_direction_8_encoding()
        labels = pd.Series(["up", "sideways"])
        preview = preview_label_encoding(labels, plan)
        self.assertTrue(preview.unknown_labels)
        with self.assertRaisesRegex(ValueError, "Unknown labels"):
            encode_labels_for_preview(labels, plan)

    def test_missing_label_produces_error(self) -> None:
        plan = default_future_direction_8_encoding()
        labels = pd.Series(["up", None])
        preview = preview_label_encoding(labels, plan)
        self.assertEqual(preview.missing_count, 1)
        with self.assertRaisesRegex(ValueError, "Missing labels"):
            encode_labels_for_preview(labels, plan)

    def test_encode_does_not_mutate_source(self) -> None:
        plan = default_future_direction_8_encoding()
        labels = pd.Series(["down", "flat", "up"])
        before = labels.copy(deep=True)
        encoded = encode_labels_for_preview(labels, plan)
        self.assertEqual(labels.tolist(), before.tolist())
        self.assertEqual(encoded.tolist(), [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
