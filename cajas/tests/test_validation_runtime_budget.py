from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_runtime_budget import (
    assess_timing_consistency,
    build_validation_runtime_budget_report,
    check_component_budget,
    check_validation_runtime_budgets,
    generate_budget_report_markdown,
    load_budget_config,
)
from cajas.scripts.check_validation_runtime_budget import main as check_budget_main


class ValidationRuntimeBudgetTests(unittest.TestCase):
    def test_component_budget_pass(self) -> None:
        """Test component budget check passes when within budget."""
        result = check_component_budget("test_component", 5.0, 10.0)
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.observed_seconds, 5.0)
        self.assertEqual(result.budget_seconds, 10.0)
        self.assertEqual(result.delta_seconds, -5.0)

    def test_component_budget_warn(self) -> None:
        """Test component budget check warns when slightly over."""
        result = check_component_budget("test_component", 11.0, 10.0, warn_threshold_ratio=1.15)
        self.assertEqual(result.status, "warn")
        self.assertGreater(result.observed_seconds, result.budget_seconds)
        self.assertLessEqual(result.ratio, 1.15)

    def test_component_budget_fail(self) -> None:
        """Test component budget check fails when significantly over."""
        result = check_component_budget("test_component", 20.0, 10.0, warn_threshold_ratio=1.15)
        self.assertEqual(result.status, "fail")
        self.assertGreater(result.ratio, 1.15)

    def test_component_budget_missing(self) -> None:
        """Test component budget check handles missing timing data."""
        result = check_component_budget("test_component", None, 10.0)
        self.assertEqual(result.status, "missing")
        self.assertIsNone(result.observed_seconds)

    def test_check_validation_runtime_budgets_pass(self) -> None:
        """Test validation runtime budget check passes."""
        timing_data = {
            "results": [
                {"name": "compileall", "seconds": 0.5},
                {"name": "pytest_fast", "seconds": 80.0},
            ],
            "total_seconds": 85.0,
        }
        budget_config = {
            "budgets_seconds": {
                "fast_total": 100.0,
                "compileall": 1.0,
                "pytest_fast": 90.0,
            },
            "warn_threshold_ratio": 1.15,
        }
        results, overall_status = check_validation_runtime_budgets(timing_data, budget_config)
        self.assertEqual(overall_status, "pass")
        self.assertEqual(len(results), 3)

    def test_check_validation_runtime_budgets_warn(self) -> None:
        """Test validation runtime budget check warns on missing required component."""
        timing_data = {
            "results": [
                {"name": "compileall", "seconds": 0.5},
            ],
            "total_seconds": 85.0,
        }
        budget_config = {
            "budgets_seconds": {
                "fast_total": 100.0,
                "compileall": 1.0,
                "pytest_fast": 90.0,
            },
            "warn_threshold_ratio": 1.15,
            "required_components": ["fast_total", "pytest_fast"],
            "optional_components": ["compileall"],
        }
        results, overall_status = check_validation_runtime_budgets(timing_data, budget_config)
        # pytest_fast is required but missing, should warn
        self.assertEqual(overall_status, "warn")

    def test_markdown_includes_key_sections(self) -> None:
        """Test Markdown report includes key sections."""
        timing_data = {
            "results": [
                {"name": "compileall", "seconds": 0.5},
            ],
            "total_seconds": 85.0,
        }
        budget_config = {
            "budgets_seconds": {
                "fast_total": 100.0,
                "compileall": 1.0,
            },
            "warn_threshold_ratio": 1.15,
        }
        results, overall_status = check_validation_runtime_budgets(timing_data, budget_config)
        markdown = generate_budget_report_markdown(results, overall_status, budget_config)

        self.assertIn("Validation Runtime Budget Report", markdown)
        self.assertIn("engineering guardrails", markdown)
        self.assertIn("not performance claims", markdown)
        self.assertIn("Component Budget Status", markdown)
        self.assertIn("Largest Deltas", markdown)
        self.assertIn("Reviewer Recommendations", markdown)

    def test_cli_exits_nonzero_on_fail(self) -> None:
        """Test CLI exits non-zero on fail status."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            budget_config = {
                "version": 1,
                "budgets_seconds": {"fast_total": 10.0},
                "warn_threshold_ratio": 1.15,
            }
            budget_path = tmp_path / "budgets.json"
            budget_path.write_text(json.dumps(budget_config), encoding="utf-8")

            timing_data = {"results": [], "total_seconds": 50.0}
            timing_path = tmp_path / "timing.json"
            timing_path.write_text(json.dumps(timing_data), encoding="utf-8")

            out_json = tmp_path / "report.json"
            out_md = tmp_path / "report.md"

            ret = check_budget_main([
                "--budgets", str(budget_path),
                "--timing-json", str(timing_path),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ])
            self.assertNotEqual(ret, 0)

    def test_cli_supports_fail_on_warn(self) -> None:
        """Test CLI supports --fail-on-warn flag."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            budget_config = {
                "version": 1,
                "budgets_seconds": {"fast_total": 100.0, "pytest_fast": 10.0},
                "warn_threshold_ratio": 1.15,
                "required_components": ["fast_total", "pytest_fast"],
                "optional_components": [],
            }
            budget_path = tmp_path / "budgets.json"
            budget_path.write_text(json.dumps(budget_config), encoding="utf-8")

            # pytest_fast is required but missing
            timing_data = {"results": [], "total_seconds": 85.0}
            timing_path = tmp_path / "timing.json"
            timing_path.write_text(json.dumps(timing_data), encoding="utf-8")

            out_json = tmp_path / "report.json"
            out_md = tmp_path / "report.md"

            ret = check_budget_main([
                "--budgets", str(budget_path),
                "--timing-json", str(timing_path),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
                "--fail-on-warn",
            ])
            self.assertNotEqual(ret, 0)

    def test_optional_components_missing_does_not_warn(self) -> None:
        """Test missing optional components do not cause overall warn."""
        timing_data = {
            "results": [],
            "total_seconds": 85.0,
        }
        budget_config = {
            "budgets_seconds": {
                "fast_total": 100.0,
                "optional_component": 10.0,
            },
            "warn_threshold_ratio": 1.15,
            "required_components": ["fast_total"],
            "optional_components": ["optional_component"],
        }
        results, overall_status = check_validation_runtime_budgets(timing_data, budget_config)
        # fast_total is measured and within budget, optional_component missing is OK
        self.assertEqual(overall_status, "pass")

    def test_timing_consistency_pass_with_fresh_metadata(self) -> None:
        timing_data = {
            "created_at": "2026-05-02T00:00:00+00:00",
            "run_id": "run-1",
            "tier": "fast",
            "timing_source": "run_fast_validation.py",
            "results": [{"name": "pytest_fast", "seconds": 80.0}],
            "total_seconds": 80.0,
        }
        budget_config = {"budgets_seconds": {"fast_total": 100.0, "pytest_fast": 90.0}, "required_components": ["fast_total", "pytest_fast"]}
        report = assess_timing_consistency(
            timing_data,
            budget_config,
            now=datetime.fromisoformat("2026-05-02T00:10:00+00:00"),
            max_age_seconds=3600,
            timing_path=None,
        )
        self.assertEqual(report["status"], "pass")

    def test_timing_consistency_warns_on_legacy_metadata_missing(self) -> None:
        timing_data = {"results": [{"name": "pytest_fast", "seconds": 80.0}], "total_seconds": 80.0}
        budget_config = {"budgets_seconds": {"fast_total": 100.0, "pytest_fast": 90.0}, "required_components": ["fast_total", "pytest_fast"]}
        report = assess_timing_consistency(timing_data, budget_config, max_age_seconds=None)
        self.assertEqual(report["status"], "warn")

    def test_timing_consistency_fails_on_negative_required(self) -> None:
        timing_data = {
            "created_at": "2026-05-02T00:00:00+00:00",
            "run_id": "run-1",
            "tier": "fast",
            "timing_source": "run_fast_validation.py",
            "results": [{"name": "pytest_fast", "seconds": -1.0}],
            "total_seconds": 80.0,
        }
        budget_config = {"budgets_seconds": {"fast_total": 100.0, "pytest_fast": 90.0}, "required_components": ["fast_total", "pytest_fast"]}
        report = assess_timing_consistency(timing_data, budget_config, max_age_seconds=None)
        self.assertEqual(report["status"], "fail")

    def test_timing_consistency_warns_on_step_total_mismatch(self) -> None:
        timing_data = {
            "created_at": "2026-05-02T00:00:00+00:00",
            "run_id": "run-1",
            "tier": "fast",
            "timing_source": "run_fast_validation.py",
            "results": [{"name": "pytest_fast", "seconds": 80.0}],
            "total_seconds": 84.0,
        }
        budget_config = {"budgets_seconds": {"fast_total": 100.0, "pytest_fast": 90.0}, "required_components": ["fast_total", "pytest_fast"]}
        report = assess_timing_consistency(timing_data, budget_config, max_age_seconds=None)
        self.assertEqual(report["status"], "warn")

    def test_budget_report_includes_timing_consistency(self) -> None:
        timing_data = {
            "created_at": "2026-05-02T00:00:00+00:00",
            "run_id": "run-1",
            "tier": "fast",
            "timing_source": "run_fast_validation.py",
            "results": [{"name": "pytest_fast", "seconds": 80.0}],
            "total_seconds": 80.0,
        }
        budget_config = {"budgets_seconds": {"fast_total": 100.0, "pytest_fast": 90.0}, "required_components": ["fast_total", "pytest_fast"]}
        report = build_validation_runtime_budget_report(timing_data, budget_config, max_age_seconds=None)
        self.assertIn("timing_consistency", report)
        self.assertEqual(report["timing_consistency"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
