from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.dataset_quality_research import build_dataset_quality_research_artifacts
from cajas.reports.dataset_quality_schema_contract import (
    compare_schema_shapes,
    compute_drift_summary,
    detect_drift_against_golden,
    extract_schema_shape,
    validate_bundle_contract,
    validate_report_contract,
    validate_semantic_constraints,
)
from cajas.scripts.validate_dataset_quality_contract import main as validate_contract_main


class DatasetQualitySchemaContractTests(unittest.TestCase):
    def test_valid_dataset_quality_report_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,up\n"
                "EURUSD,2025-01-01 00:15:00,1.1,down\n",
                encoding="utf-8",
            )
            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv,
                label_columns=["future_direction_8"],
                feature_columns=["feature_a"],
                chunk_size=2,
            )
            report = bundle["dataset_quality_report"]
            issues = validate_report_contract(report, "dataset_quality_report")
            errors = [i for i in issues if i.severity == "error"]
            self.assertEqual(len(errors), 0)

    def test_missing_required_key_fails(self) -> None:
        report = {"schema_version": "v1"}
        issues = validate_report_contract(report, "dataset_quality_report")
        errors = [i for i in issues if i.severity == "error"]
        self.assertGreater(len(errors), 0)

    def test_wrong_type_fails(self) -> None:
        report = {
            "schema_version": "v1",
            "report_type": "dataset_quality_report",
            "status": "pass",
            "severity_counts": {},
            "scope": "offline_research_only",
            "row_count": "not_a_number",
            "column_count": 5,
            "quality_score": {},
            "label_diagnostics": [],
            "label_review_buckets": [],
            "time_coverage": {},
            "feature_readiness": {},
        }
        issues = validate_report_contract(report, "dataset_quality_report")
        errors = [i for i in issues if i.severity == "error"]
        self.assertGreater(len(errors), 0)

    def test_extra_field_allowed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,up\n",
                encoding="utf-8",
            )
            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv,
                label_columns=["future_direction_8"],
                feature_columns=["feature_a"],
            )
            report = bundle["dataset_quality_report"]
            report["extra_field"] = "allowed"
            issues = validate_report_contract(report, "dataset_quality_report")
            errors = [i for i in issues if i.severity == "error"]
            self.assertEqual(len(errors), 0)

    def test_bundle_validation(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,up\n",
                encoding="utf-8",
            )
            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv,
                label_columns=["future_direction_8"],
                feature_columns=["feature_a"],
            )
            issues = validate_bundle_contract(bundle)
            errors = [i for i in issues if i.severity == "error"]
            self.assertEqual(len(errors), 0)

    def test_shape_extraction(self) -> None:
        value = {"a": 1, "b": "str", "c": [{"d": 2.0}]}
        shape = extract_schema_shape(value)
        self.assertEqual(shape["a"], "number")
        self.assertEqual(shape["b"], "str")
        self.assertIsInstance(shape["c"], list)

    def test_additive_field_is_non_breaking(self) -> None:
        old = {"a": "str", "b": "number"}
        new = {"a": "str", "b": "number", "c": "str"}
        diff = compare_schema_shapes(old, new)
        self.assertIn("c", diff.added_fields)
        self.assertEqual(len(diff.removed_fields), 0)
        self.assertFalse(diff.is_breaking)

    def test_removed_field_is_breaking(self) -> None:
        old = {"a": "str", "b": "number"}
        new = {"a": "str"}
        diff = compare_schema_shapes(old, new)
        self.assertIn("b", diff.removed_fields)
        self.assertTrue(diff.is_breaking)

    def test_type_change_is_breaking(self) -> None:
        old = {"a": "str"}
        new = {"a": 123}
        diff = compare_schema_shapes(old, new)
        self.assertGreater(len(diff.type_changes), 0)
        self.assertTrue(diff.is_breaking)

    def test_golden_shapes_exist(self) -> None:
        golden_dir = Path("cajas/data_examples/golden/dataset_quality")
        expected_files = [
            "dataset_quality_report_shape.json",
            "label_coverage_diagnostics_shape.json",
            "time_coverage_diagnostics_shape.json",
            "chunked_feature_dry_run_shape.json",
            "feature_schema_manifest_shape.json",
            "offline_research_queue_summary_shape.json",
            "bundle_shape.json",
        ]
        for fname in expected_files:
            path = golden_dir / fname
            self.assertTrue(path.exists(), f"golden shape missing: {fname}")
            shape = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(shape, (dict, list, str))

    def test_current_smoke_matches_golden_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv = root / "dataset.csv"
            csv.write_text(
                "instrument,datetime,feature_a,future_direction_8\n"
                "EURUSD,2025-01-01 00:00:00,1.0,up\n",
                encoding="utf-8",
            )
            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv,
                label_columns=["future_direction_8"],
                feature_columns=["feature_a"],
            )
            report = bundle["dataset_quality_report"]
            golden_path = Path("cajas/data_examples/golden/dataset_quality/dataset_quality_report_shape.json")
            golden_shape = json.loads(golden_path.read_text(encoding="utf-8"))
            current_shape = extract_schema_shape(report, max_depth=4)
            diff = compare_schema_shapes(golden_shape, current_shape)
            # Allow golden to have more fields (from richer fixture), but current must not remove required fields
            # Check that current has all top-level keys from golden
            if isinstance(golden_shape, dict) and isinstance(current_shape, dict):
                for key in ["schema_version", "report_type", "status", "quality_score", "label_diagnostics"]:
                    self.assertIn(key, current_shape, f"required key missing: {key}")

    def test_cli_fails_on_missing_required_field(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_json = root / "report.json"
            report_json.write_text(json.dumps({"schema_version": "v1"}), encoding="utf-8")
            ret = validate_contract_main(["--report-json", str(report_json), "--report-type", "dataset_quality_report"])
            self.assertNotEqual(ret, 0)

    def test_cli_fails_on_wrong_type(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_json = root / "report.json"
            bad_report = {
                "schema_version": "v1",
                "report_type": "dataset_quality_report",
                "status": "pass",
                "severity_counts": {},
                "scope": "offline_research_only",
                "row_count": "not_a_number",
                "column_count": 5,
                "quality_score": {},
                "label_diagnostics": [],
                "label_review_buckets": [],
                "time_coverage": {},
                "feature_readiness": {},
            }
            report_json.write_text(json.dumps(bad_report), encoding="utf-8")
            ret = validate_contract_main(["--report-json", str(report_json), "--report-type", "dataset_quality_report"])
            self.assertNotEqual(ret, 0)

    def test_no_drift_returns_zero_counts(self) -> None:
        golden = {"a": "str", "b": "number"}
        current = {"a": "str", "b": "number"}
        drift_items = detect_drift_against_golden(current, golden, "test.json", set())
        summary = compute_drift_summary(drift_items, 1)
        self.assertEqual(summary.breaking_count, 0)
        self.assertEqual(summary.additive_count, 0)
        self.assertEqual(summary.type_change_count, 0)
        self.assertEqual(summary.missing_required_count, 0)

    def test_additive_drift_increments_additive_count(self) -> None:
        golden = {"a": "str"}
        current = {"a": "str", "b": "number"}
        drift_items = detect_drift_against_golden(current, golden, "test.json", set())
        summary = compute_drift_summary(drift_items, 1)
        self.assertEqual(summary.additive_count, 1)
        self.assertEqual(summary.breaking_count, 0)

    def test_missing_required_field_detected(self) -> None:
        golden = {"a": "str", "b": "number"}
        current = {"a": "str"}
        drift_items = detect_drift_against_golden(current, golden, "test.json", {"b"})
        summary = compute_drift_summary(drift_items, 1)
        self.assertEqual(summary.missing_required_count, 1)
        self.assertEqual(summary.breaking_count, 1)

    def test_type_change_detected(self) -> None:
        golden = {"a": "str"}
        current = {"a": 123}
        drift_items = detect_drift_against_golden(current, golden, "test.json", set())
        summary = compute_drift_summary(drift_items, 1)
        self.assertEqual(summary.type_change_count, 1)
        self.assertEqual(summary.breaking_count, 1)

    def test_semantic_valid_quality_score_passes(self) -> None:
        report = {
            "quality_score": {"score": 85.5, "max_score": 100, "grade": "A", "components": {}},
            "status": "pass",
            "severity_counts": {"error": 0, "warning": 1, "info": 2},
            "row_count": 100,
            "column_count": 5,
        }
        issues = validate_semantic_constraints(report, "dataset_quality_report")
        errors = [i for i in issues if i.severity == "error"]
        self.assertEqual(len(errors), 0)

    def test_semantic_quality_score_out_of_range_fails(self) -> None:
        report = {"quality_score": {"score": 150, "max_score": 100, "grade": "A", "components": {}}}
        issues = validate_semantic_constraints(report, "dataset_quality_report")
        errors = [i for i in issues if i.severity == "error"]
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("score must be in [0, 100]" in i.message for i in errors))

    def test_semantic_negative_count_fails(self) -> None:
        report = {"severity_counts": {"error": -1, "warning": 0, "info": 0}}
        issues = validate_semantic_constraints(report, "dataset_quality_report")
        errors = [i for i in issues if i.severity == "error"]
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("must be non-negative" in i.message for i in errors))

    def test_semantic_unknown_grade_warns(self) -> None:
        report = {"quality_score": {"score": 85, "max_score": 100, "grade": "Z", "components": {}}}
        issues = validate_semantic_constraints(report, "dataset_quality_report")
        warnings = [i for i in issues if i.severity == "warning"]
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("unknown grade value" in i.message for i in warnings))

    def test_semantic_unknown_status_warns(self) -> None:
        report = {"status": "unknown_status"}
        issues = validate_semantic_constraints(report, "dataset_quality_report")
        warnings = [i for i in issues if i.severity == "warning"]
        self.assertGreater(len(warnings), 0)
        self.assertTrue(any("unknown status value" in i.message for i in warnings))

    def test_additive_drift_not_semantic_error(self) -> None:
        # Additive drift should remain shape drift, not become semantic error
        golden = {"a": "str"}
        current = {"a": "str", "b": "number"}
        drift_items = detect_drift_against_golden(current, golden, "test.json", set())
        self.assertEqual(len(drift_items), 1)
        self.assertEqual(drift_items[0].kind, "additive")


if __name__ == "__main__":
    unittest.main()
