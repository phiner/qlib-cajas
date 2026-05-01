from __future__ import annotations

import json
import unittest

from cajas.qlib_compat.class_resolver import resolve_dotted_path, resolve_dotted_paths


class ClassResolverTests(unittest.TestCase):
    def test_resolves_stdlib_object(self) -> None:
        result = resolve_dotted_path("json.dumps")
        self.assertTrue(result.resolved)
        self.assertEqual(result.module_path, "json")
        self.assertEqual(result.attribute_name, "dumps")

    def test_resolves_project_object(self) -> None:
        result = resolve_dotted_path("cajas.datasets.prepared_dataset.PreparedDataset")
        self.assertTrue(result.resolved)

    def test_missing_module(self) -> None:
        result = resolve_dotted_path("missing_mod_xyz.Object")
        self.assertFalse(result.resolved)
        self.assertIsNotNone(result.import_error)

    def test_missing_attribute(self) -> None:
        result = resolve_dotted_path("json.not_real_attribute")
        self.assertFalse(result.resolved)
        self.assertIsNotNone(result.import_error)

    def test_report_serialization(self) -> None:
        report = resolve_dotted_paths([
            "json.dumps",
            "json.not_real_attribute",
        ])
        payload = report.to_dict()
        json.dumps(payload)
        self.assertIn("results", payload)
        self.assertIn("unresolved", payload)


if __name__ == "__main__":
    unittest.main()
